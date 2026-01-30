#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Get MD5 of the analysed files of a given user.

Usage:
    python3 get_files_md5_of_user.py <gorille-api-url> <your-username> <your-password> <username> [limit]
"""

import os
import sys

from pyape import init_ape_session
from pyape import ApeException


DEFAULT_LIMIT = 50


def iter_user_files(ape, user_id: str):
    """
    Iterate over all files analysed by a user using pagination.
    """
    offset = 0

    while True:
        # print(f"Get analysis history of {user_id} with offset={offset} and limit={DEFAULT_LIMIT}")
        resp = ape.get_user_history(
            user_id=user_id,
            offset=offset,
            limit=DEFAULT_LIMIT,
        )

        if resp.data is None:
            print("[!] No data ?!")
            sys.exit(1)

        items = resp.data
        if len(items) == 0:
            # print("No more hisotry to grab")
            return
        else:
            pass
            # print(f"Grabbed {len(items)} analysed files from history")

        for item in items:
            yield item

        offset += DEFAULT_LIMIT


def print_user_files(ape, user_id: str, max_files: int | None):

    handled = 0

    for entry in iter_user_files(ape, user_id):
        if max_files is not None and handled >= max_files:
            break

        file_id = entry.id

        try:
            attributes = entry.attributes or {}
            # filename = attributes["filename"]
            file_md5 = attributes["md5"]
            print(file_md5)
        except ApeException as e:
            print(f"[!] Error with file ID {file_id} (boarded): {e}")
            sys.exit(1)

        handled += 1


def main():
    if len(sys.argv) < 5:
        print(
            "Usage: python3 get_files_md5_of_user.py <gorille-api-url> <your-username> <your-password> <username> [limit]"
        )
        print(
            "eg: python3 get_files_md5_of_user.py https://demo.gorille.tech/api me my-password paul 10"
        )
        sys.exit(1)

    gorille_api_url = sys.argv[1]
    my_username = sys.argv[2]
    my_password = sys.argv[3]
    username = sys.argv[4]

    max_files = None
    if len(sys.argv) >= 6:
        try:
            max_files = int(sys.argv[5])
        except ValueError:
            print("Error: limit must be an integer")
            sys.exit(1)


    # Use default credentials / URL
    ape = init_ape_session(url=gorille_api_url, username=my_username, password=my_password)

    print_user_files(
        ape=ape,
        user_id=username,
        max_files=max_files,
    )


if __name__ == "__main__":
    main()
