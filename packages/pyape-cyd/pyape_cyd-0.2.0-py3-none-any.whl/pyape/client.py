# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "Cyber-Detect"

import json
import os
import re
from typing import Any, Optional

import requests
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from websocket import create_connection


class Md5(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: Any):
        if not isinstance(v, str):
            raise TypeError("Invalid MD5 (not a string)")
        if not re.findall("^[0-9a-f]{32}$", v):
            raise ValueError("Invalid MD5 (wrong format)")
        return cls(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `str`
        return handler(core_schema.str_schema())


class Sha256(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: Any) -> Sha256:
        if not isinstance(v, str):
            raise TypeError("Invalid SHA256 (not a string)")
        if not re.findall("^[0-9a-f]{64}$", v):
            raise ValueError("Invalid SHA256 (wrong format)")
        return cls(v)


    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `str`
        return handler(core_schema.str_schema())



class ApeException(Exception):
    """Base class exception for pyape package."""

    pass


# Here we define models used to represent
# JSON:API objects defined in https://jsonapi.org/format/
# (this is the specification that we use, the same as VirusTotal)

##############################################
# Response models
##############################################


class ApeData(BaseModel):
    type: str
    id: str | None = None
    attributes: Any | None  # attributes member is optionnal
    relationships: dict | None = None

    # Any other member is forbidden
    model_config = ConfigDict(extra='forbid')


# See https://jsonapi.org/format/#document-links
class ApeLinks(BaseModel):
    self: AnyHttpUrl
    next: AnyHttpUrl | None = None
    prev: AnyHttpUrl | None = None
    first: AnyHttpUrl | None = None
    last: AnyHttpUrl | None = None

    # Any other member is forbidden
    model_config = ConfigDict(extra='forbid')


class ApeError(BaseModel):
    status: str  # the HTTP status code applicable to this problem, expressed as a string value.
    code: str | None = (
        None  # an application-specific error code, expressed as a string value.
    )
    title: str  # a short, human-readable summary of the problem that SHOULD NOT change from occurrence to occurrence of the problem, except for purposes of localization.
    detail: str | None = (
        None  # a human-readable explanation specific to this occurrence of the problem.
    )
    meta: Any | None = (
        None  # a meta object containing non-standard meta-information about the error.
    )

class ApeResponse(BaseModel):
    data: ApeData | list[ApeData] | None = None  # If 'error' is None 'data' should not be None. Also, If 'data' is None 'error' should not be None
    error: ApeError | None = None
    meta: Any | None = None
    links: ApeLinks | None = None

    http_status_code: int # The HTTP status code of the request

    # Any other member is forbidden
    model_config = ConfigDict(extra='forbid')

    # def pprint(self) -> None:
    #     import pprint
    #     pprint.pprint(self.resp)

    def to_dict(self) -> dict:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    def get_type(self) -> str | None:
        if self.data is not None and type(self.data) is ApeData:
            return self.data.type
        return None

    def get_id(self) -> str | None:
        if self.data is not None and type(self.data) is ApeData:
            return self.data.id
        return None

    def get_attributes(self):
        if self.data is not None and type(self.data) is ApeData:
            return self.data.attributes
        return None

    def get_attribute(self, attribute: str):
        if self.data is not None and type(self.data) is ApeData:
            if self.data.attributes is not None:
                return self.data.attributes.get(attribute)
        return None

    def get_category(self):
        return self.get_attribute("category")

    def get_protection(self):
        return self.get_attribute("protection")

    def get_file_analysis(self, analysis_method: str):
        analyses = self.get_attribute("analyses")
        if analyses is not None:
            return analyses[analysis_method]
        return None

    def get_file_analysis_result(self, analysis_method: str):
        analysis = self.get_file_analysis(analysis_method)
        if analysis is not None:
            return analysis.get("result")
        return None

    def get_file_analyses(self):
        return self.get_attribute("analyses")

class Ape:
    def __init__(
        self,
        url: str = "http://localhost/api",
        apikey: str | None = None,
        username: str | None = "user",
        password: str | None = "user",
    ):
        # Remove traling slash if any
        if url.endswith("/"):
            url = url[:-1]

        self._url = url
        if self._url.startswith("https://"):
            self._ws_url = self._url.replace("https", "wss") + "/v2/ws"
        else:
            self._ws_url = self._url.replace("http", "ws") + "/v2/ws"

        self._ws_connection = None
        self.apikey = apikey

        self._session = requests.Session()
        if apikey is not None:
            self._session.headers = {'x-apikey': apikey}
        elif username is not None and password is not None:
            self._session.auth = (username, password)

    def _build_ape_response(self, r: requests.Response) -> ApeResponse:
        if r.content == b'':  # Special case for a delete (no content)
            return ApeResponse(
                http_status_code=r.status_code,
            )
        try:
            resp = r.json()
        except json.JSONDecodeError:
            raise ApeException("Failed to decode APE response as a valid JSON (HTTP status code: {}, raw response: {})".format(r.status_code, str(r.content)))
        return ApeResponse(
            **resp,
            http_status_code=r.status_code,
        )

    def _build_dict(self, r: requests.Response, return_dict: bool = False) -> dict:
        if r.content == b'':  # Special case for a delete (no content)
            return {}
        try:
            resp = r.json()
            return resp
        except json.JSONDecodeError:
            raise ApeException("Failed to decode APE response as a valid JSON (HTTP status code: {}, raw response: {})".format(r.status_code, str(r.content)))

    def _post(self, route: str, params={}, files=None, json=None, data=None) -> ApeResponse:
        url = self._url + route
        try:
            r = self._session.post(url, params=params, files=files, json=json, data=data)
            return self._build_ape_response(r)
        except Exception as e:
            raise ApeException(e)

    def _get(self, route: str, params={}) -> ApeResponse:
        url = self._url + route
        try:
            r = self._session.get(url, params=params)
            return self._build_ape_response(r)
        except Exception as e:
            raise ApeException(e)

    def _get_dict(self, route: str, params={}) -> dict:
        url = self._url + route
        try:
            r = self._session.get(url, params=params)
            return self._build_dict(r)
        except Exception as e:
            raise ApeException(e)

    def _get_content(self, route: str, params={}) -> bytes:
        url = self._url + route
        try:
            r = self._session.get(url, params=params)
            return r.content
        except Exception as e:
            raise ApeException(e)

    def _put(self, route: str, params={}) -> ApeResponse:
        url = self._url + route
        try:
            r = self._session.put(url, params=params)
            return self._build_ape_response(r)
        except Exception as e:
            raise ApeException(e)

    def _delete(self, route: str, params={}) -> ApeResponse:
        url = self._url + route
        try:
            r = self._session.delete(url, params=params)
            return self._build_ape_response(r)
        except Exception as e:
            raise ApeException(e)

    def _patch(self, route: str, params={}, json=None) -> ApeResponse:
        url = self._url + route
        try:
            r = self._session.patch(url, params=params, json=json)
            return self._build_ape_response(r)
        except Exception as e:
            raise ApeException(e)

    def get_status_code(self, route, params={}) -> int:
        url = self._url + route
        r = self._session.get(url, params=params)
        return r.status_code



    ################################
    # APE Websocket stuff
    ################################

    def create_ws_connection(self, apikey: Optional[str]):
        """Initiate a new WS connection with APE"""
        if apikey is not None:
            url = self._ws_url + "?apikey=" + apikey
        else:
            url = self._ws_url
        self._ws_connection = create_connection(url)


    def send_ws_json(self, msg: dict) -> None:
        """Send a JSON message to an already instanciated WS connection"""
        if self._ws_connection is None:
            raise Exception("Websocket not connected")
        self._ws_connection.send(json.dumps(msg))

    def recv_ws_json(self) -> dict:
        """Receive a JSON message from an already instanciated WS connection"""
        if self._ws_connection is None:
            raise Exception("Websocket not connected")
        r = self._ws_connection.recv()
        return json.loads(r)

    def ws_subscribe_task(self, task_id: str) -> None:
        msg = {
            "event": "task_subscribe",
            "data": {
                "task_id": task_id,
           }
        }
        self.send_ws_json(msg)

    ################################
    # APE routes
    ################################

    def about(self) -> ApeResponse:
        route = "/v2/about"
        return self._get(route)

    ################################
    # APE /files routes
    ################################
    def post_file_by_upload(
        self,
        filepath: str,
        subpath: str = "",
        force: bool = False,
        details: bool = False,
        extract: bool = True,
        early_exit: bool = False,
        password: str | None = None
    ) -> ApeResponse:
        route = "/v2/files{}".format(subpath)
        params = {
            "details": details,
            "force": force,
            "extract": extract,
            "early_exit": early_exit,
            "password": password,
        }
        files = {
            'file': (os.path.basename(filepath), open(filepath, "rb"), 'application/octet-stream')
        }
        return self._post(route, params=params, files=files)

    def post_file_by_id(
        self,
        file_id: str,
        subpath: str,
        force: bool = False,
        details: bool = False,
        extract: bool = True,
        early_exit: bool = False,
        password: str | None = None
    ) -> ApeResponse:
        route = "/v2/files/{}{}".format(file_id, subpath)
        params = {
            "details": details,
            "force": force,
            "extract": extract,
            "early_exit": early_exit,
            "password": password,
        }
        return self._post(route, params=params)

    def post_file_orion(
        self,
        filepath: str,
    ) -> ApeResponse:
        route = "/v2/files"
        params = {
            "path": filepath,
        }
        return self._post(route, params=params)

    def get_file(self, file_id: str, subpath: str = "", details: bool = False) -> ApeResponse:
        route = "/v2/files/{}{}".format(file_id, subpath)
        params = {
            "details": details,
        }
        return self._get(route, params=params)

    def get_file_3d_graph(self, file_id: str, black: bool = True, white: bool = True, small: bool = False) -> dict:
        route = "/v2/files/{}/3d_graph".format(file_id)
        params = {
            "black": black,
            "white": white,
            "small": small,
        }
        return self._get_dict(route, params=params)

    def get_file_3d_graph_screenshots(self, file_id: str, n: int = 1) -> dict:
        route = "/v2/files/{}/3d_graph/screenshot".format(file_id)
        params = {
            "n": n
        }
        return self._get_dict(route, params=params)

    def get_file_report(self, file_id: str) -> bytes:
        route = "/v2/files/{}/report".format(file_id)
        return self._get_content(route, params={})

    def get_file_download(self, file_id: str) -> bytes:
        route = "/v2/files/{}/download".format(file_id)
        return self._get_content(route, params={})

    def get_file_analysis(self, file_id: str, analysis_engine: str, subpath: str = "") -> ApeResponse:
        route = "/v2/files/{}/analyses/{}{}".format(file_id, analysis_engine, subpath)
        return self._get(route)

    ################################
    # APE /tasks routes
    ################################
    def get_task(self, task_id: str) -> ApeResponse:
        route = "/v2/tasks/{}".format(task_id)
        return self._get(route)

    ################################
    # APE /users routes
    ################################
    def get_user(self, user_id: str = "me", subpath: str = "", params: dict = {}) -> ApeResponse:
        route = "/v2/users/{}{}".format(user_id, subpath)
        return self._get(route, params=params)

    def put_user(self, user_id: str, subpath: str = "") -> ApeResponse:
        route = "/v2/users/{}{}".format(user_id, subpath)
        return self._put(route)

    def delete_user(self, user_id: str, subpath: str = "") -> ApeResponse:
        route = "/v2/users/{}{}".format(user_id, subpath)
        return self._delete(route)

    def post_user(
        self,
        username: str,
        password: str,
        firstname: str,
        lastname: str,
        email: str,
        user_group: str,
        is_admin: bool = False,
    ) -> ApeResponse:
        route = "/v2/users"
        params = {
            "username": username,
            "password": password,
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "user_group": user_group,
            "is_admin": is_admin,
        }
        return self._post(route, params=params)

    def put_user_add_tokens(
        self,
        user_id: str,
        tokens: int,
        user_group_id: Optional[str] = None,
    ) -> ApeResponse:
        route = "/v2/users/{}/add_tokens".format(user_id)
        params: dict[str, Any] = {
            "tokens": tokens,
        }
        if user_group_id is not None:
            params["user_group_id"] = user_group_id
        return self._put(route, params=params)

    def delete_user_history(self, user_id: str, limit: Optional[int] = None) -> ApeResponse:
        route = "/v2/users/{}/history".format(user_id)
        params = {}
        if limit is not None:
            params["limit"] = limit
        return self._delete(route, params=params)

    def get_user_history(
        self,
        filename: Optional[str] = None,
        file_hash: Optional[str] = None,
        category: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
        user_id: str = "me"
    ) -> ApeResponse:
        route = "/v2/users/{}/history".format(user_id)
        params = {
            "filename": filename,
            "file_hash": file_hash,
            "category": category,
            "offset": offset,
            "limit": limit,
            "sort": sort,
        }
        return self._get(route, params=params)

    ################################
    # APE /malware routes
    ################################
    def get_malware(self, malware_name: str) -> ApeResponse:
        route = "/v2/malware/{}".format(malware_name)
        return self._get(route)

    ################################
    # APE /user_groups routes
    ################################
    def get_user_group(self, user_group_id: str, subpath: str = "", params: dict = {}) -> ApeResponse:
        route = "/v2/user_groups/{}{}".format(user_group_id, subpath)
        return self._get(route, params=params)

    def get_user_group_history(
        self,
        user_group: str,
        filename: Optional[str] = None,
        file_hash: Optional[str] = None,
        category: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> ApeResponse:
        route = "/v2/user_groups/{}/history".format(user_group)
        params = {
            "filename": filename,
            "file_hash": file_hash,
            "category": category,
            "offset": offset,
            "limit": limit,
            "sort": sort,
        }
        return self._get(route, params=params)

    ################################
    # APE /files/{}/comments routes
    ################################
    def get_file_comments(self, file_hash: Md5 | Sha256) -> ApeResponse:
        route = "/v2/files/{}/comments".format(file_hash)
        return self._get(route)

    def post_file_comment(self, file_hash: Md5 | Sha256, comment: str) -> ApeResponse:
        route = "/v2/files/{}/comments".format(file_hash)
        data = {
            "comment": comment
        }
        return self._post(route, json=data)


    ################################
    # Patrol main routes
    ################################
    def patrol_about(self) -> ApeResponse:
        route = "/patrol/v1/about"
        return self._get(route)


    ################################
    # Patrol /file-filters routes
    ################################
    def get_patrol_file_filters(self, file_sha256: Sha256 | None = None) -> ApeResponse:
        route = "/patrol/v1/file-filters"
        params = {}
        if file_sha256 is not None:
            params["file_sha256"] = file_sha256
        return self._get(route, params=params)

    def post_patrol_file_filter(self, file_filter: dict) -> ApeResponse:
        route = "/patrol/v1/file-filters"
        return self._post(route, json=file_filter)

    ################################
    # Patrol /agent-filters routes
    ################################
    def get_patrol_agent_filters(self) -> ApeResponse:
        route = "/patrol/v1/agent-filters"
        return self._get(route)

    def get_patrol_agent_filter(self, agent_filter_id: str) -> ApeResponse:
        route = "/patrol/v1/agent-filters/{}".format(agent_filter_id)
        return self._get(route)

    def post_patrol_agent_filter(self, agent_filter: dict) -> ApeResponse:
        route = "/patrol/v1/agent-filters"
        return self._post(route, json=agent_filter)

    def patch_patrol_agent_filter(self, agent_filter_id: str, agent_filter_patch: dict) -> ApeResponse:
        route = "/patrol/v1/agent-filters/{}".format(agent_filter_id)
        return self._patch(route, json=agent_filter_patch)

    ################################
    # Patrol /campaigns routes
    ################################
    def get_patrol_campaigns(self, limit: int | None = None) -> ApeResponse:
        route = "/patrol/v1/campaigns"
        params = {}
        if limit is not None:
            params["limit"] = limit
        return self._get(route, params=params)

    def get_patrol_campaign(self, campaign_id: str) -> ApeResponse:
        route = "/patrol/v1/campaigns/{}".format(campaign_id)
        return self._get(route)

    def post_patrol_campaign(self, campaign: dict) -> ApeResponse:
        route = "/patrol/v1/campaigns"
        return self._post(route, json=campaign)

    def patch_patrol_campaign(self, campaign_id: str, campaign_patch: dict) -> ApeResponse:
        route = "/patrol/v1/campaigns/{}".format(campaign_id)
        return self._patch(route, json=campaign_patch)

    def get_patrol_campaign_files(self, campaign_id: str) -> ApeResponse:
        route = "/patrol/v1/campaigns/{}/files".format(campaign_id)
        return self._get(route)

    ################################
    # Patrol /agents routes
    ################################
    def post_patrol_agent(self, agent: dict) -> ApeResponse:
        route = "/patrol/v1/agents"
        return self._post(route, json=agent)

    def get_patrol_agent(self, agent_id: str) -> ApeResponse:
        route = "/patrol/v1/agents/{}".format(agent_id)
        return self._get(route)

    def get_patrol_agent_files(self, agent_id: str) -> ApeResponse:
        route = "/patrol/v1/agents/{}/files".format(agent_id)
        return self._get(route)

    def get_patrol_agents(self) -> ApeResponse:
        route = "/patrol/v1/agents"
        return self._get(route)

    def get_patrol_agent_current_campaign(self, agent_id: str) -> ApeResponse:
        route = "/patrol/v1/agents/{}/campaigns/current".format(agent_id)
        return self._get(route)

    def post_patrol_agent_campaign_scan(self, agent_id: str, campaign_id: str) -> ApeResponse:
        route = "/patrol/v1/agents/{}/campaigns/{}/scans".format(agent_id, campaign_id)
        return self._post(route)

    def get_patrol_agent_campaign_scan(self, agent_id: str, campaign_id: str) -> ApeResponse:
        route = "/patrol/v1/agents/{}/campaigns/{}/scans".format(agent_id, campaign_id)
        return self._get(route)

    def get_or_post_patrol_scan(self, agent_id: str, campaign_id: str) -> ApeResponse:
        r = self.get_patrol_agent_campaign_scan(agent_id, campaign_id)
        if r.http_status_code == 404:
            return self.post_patrol_agent_campaign_scan(agent_id, campaign_id)
        else:
            return r

    def patch_patrol_agent(self, agent_id: str, agent_patch: dict) -> ApeResponse:
        route = "/patrol/v1/agents/{}".format(agent_id)
        return self._patch(route, json=agent_patch)

    ################################
    # Patrol /tasks routes
    ################################
    def get_patrol_task(self, task_id: str) -> ApeResponse:
        route = "/patrol/v1/tasks/{}".format(task_id)
        return self._get(route)

    ################################
    # Patrol /scans routes
    ################################
    def get_patrol_scan_files(self, scan_id: str) -> ApeResponse:
        route = "/patrol/v1/scans/{}/files".format(scan_id)
        return self._get(route)

    def get_patrol_scan(self, scan_id: str) -> ApeResponse:
        route = "/patrol/v1/scans/{}".format(scan_id)
        return self._get(route)

    def get_patrol_scans(self) -> ApeResponse:
        route = "/patrol/v1/scans"
        return self._get(route)

    def patch_patrol_scan(self, scan_id: str, scan_patch: dict) -> ApeResponse:
        route = "/patrol/v1/scans/{}".format(scan_id)
        return self._patch(route, json=scan_patch)

    def post_patrol_file_by_sha256(self, scan_id: str, file_sha256: str, filepath: str) -> ApeResponse:
        meta = {
            "filepath": filepath
        }
        route = "/patrol/v1/scans/{}/files/{}".format(scan_id, file_sha256)
        return self._post(route, json=meta)

    def post_patrol_file_by_upload(self, scan_id: str, filepath: str) -> ApeResponse:
        files = {
            'file': (os.path.basename(filepath), open(filepath, "rb"), 'application/octet-stream')
        }
        meta = {
            "filepath": filepath
        }
        # When uploading a file, you cannot also add a json, this is why we use data here.
        # see https://fastapi.tiangolo.com/tutorial/request-forms/#about-form-fields
        route = "/patrol/v1/scans/{}/files".format(scan_id)
        return self._post(route, files=files, data=meta)

    def post_patrol_file_by_sha256_or_upload(self, scan_id: str, file_sha256: str, filepath: str) -> ApeResponse:
        r = self.post_patrol_file_by_sha256(scan_id, file_sha256, filepath)
        if r.http_status_code == 404:
            return self.post_patrol_file_by_upload(scan_id, filepath)
        else:
            return r


ape = None

def init_ape_session(
    url: str = "http://localhost/api",
    apikey: str | None = None,
    username: str | None = "user",
    password: str | None = "user",
) -> Ape:
    global ape
    ape = Ape(url, apikey, username, password)
    return ape

def get_ape_session() -> Ape:
    global ape
    if ape is None:
        raise ApeException("Please init shared session first with 'init_ape_session'")
    return ape
