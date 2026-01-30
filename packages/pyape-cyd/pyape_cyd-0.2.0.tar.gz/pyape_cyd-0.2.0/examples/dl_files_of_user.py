#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Download analysed files of a given user.

Usage:
    python3 dl_files_of_user.py <gorille-api-url> <your-username> <your-password> <username> <dest_folder> [limit]
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


def download_user_files(ape, user_id: str, output_dir: str, max_files: int | None):
    """
    Download analysed files of a user.
    """
    os.makedirs(output_dir, exist_ok=True)

    downloaded = 0

    for entry in iter_user_files(ape, user_id):
        if max_files is not None and downloaded >= max_files:
            break

        file_id = entry.id

        try:
            attributes = entry.attributes or {}
            filename = attributes["filename"]
            file_md5 = attributes["md5"]
            out_directory = os.path.join(output_dir, file_md5)
            os.makedirs(out_directory, exist_ok=True)
            out_path = os.path.join(out_directory, filename)

            print(f"[{downloaded}] Downloading file ID {file_id} in {out_path}...")

            content = ape.get_file_report(file_id)
            with open(out_path, "wb") as f:
                f.write(content)
        except ApeException as e:
            print(f"[!] Failed to download file ID {file_id}: {e}")
            continue

        downloaded += 1


def main():
    if len(sys.argv) < 6:
        print(
            "Usage: python3 dl_files_of_user.py <gorille-api-url> <your-username> <your-password> <username> <dest_folder> [limit]"
        )
        print(
            "eg: python3 dl_files_of_user.py https://demo.gorille.tech/api me my-password paul /tmp/paul_files 10"
        )
        sys.exit(1)

    gorille_api_url = sys.argv[1]
    my_username = sys.argv[2]
    my_password = sys.argv[3]
    username = sys.argv[4]
    dest_folder = sys.argv[5]

    max_files = None
    if len(sys.argv) >= 7:
        try:
            max_files = int(sys.argv[6])
        except ValueError:
            print("Error: limit must be an integer")
            sys.exit(1)

    if max_files is None:
        print(f"Download all analysed files of {username} in {dest_folder}")
    else:
        print(f"Download the {max_files} latest analysed files of {username} in {dest_folder}")

    # Use default credentials / URL
    ape = init_ape_session(url=gorille_api_url, username=my_username, password=my_password)

    download_user_files(
        ape=ape,
        user_id=username,
        output_dir=dest_folder,
        max_files=max_files,
    )


if __name__ == "__main__":
    main()
