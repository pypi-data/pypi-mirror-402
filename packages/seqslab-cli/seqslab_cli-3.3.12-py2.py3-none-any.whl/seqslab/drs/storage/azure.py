# Standard Library
import asyncio
import datetime
import hashlib
import json
import os
import time
from base64 import b64encode
from functools import lru_cache
from hashlib import md5
from io import BytesIO
from typing import NoReturn
from xml.etree import ElementTree

import arrow
import requests
from aiohttp import ClientResponseError
from nubia import context
from numba import njit
from numba.typed import List
from seqslab.auth.commands import BaseAuth
from seqslab.drs import API_HOSTNAME
from yarl import URL

from .base import BaseBlob

"""
Copyright (C) 2022, Atgenomix Incorporated.

All Rights Reserved.

This program is an unpublished copyrighted work which is proprietary to
Atgenomix Incorporated and contains confidential information that is not to
be reproduced or disclosed to any other person or entity without prior
written consent from Atgenomix, Inc. in each and every instance.

Unauthorized reproduction of this program as well as unauthorized
preparation of derivative works based upon the program or distribution of
copies by sale, rental, lease or lending are violations of federal copyright
laws and state trade secret laws, punishable by civil and criminal penalties.
"""


class BlobStorage(BaseBlob):
    """
    Azure Blob service stores text and binary data as objects in the cloud.
    The Blob service offers the following three resources:
    the storage account, containers, and blobs.
    """

    TOKENS_KEY = "Microsoft.Storage/storageAccounts"
    BLOB_SERVICE_URL = "https://{account}.blob.core.windows.net"

    def __init__(self, workspace):
        self.upload_success = 0
        self.download_success = 0
        self.buffer = {}
        super().__init__(workspace)

    @lru_cache(maxsize=16)
    def refresh_token(self, uri: URL, **kwargs):
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        query_param = uri.human_repr()
        try:
            with requests.get(
                BaseBlob.DRS_REFRESH_SAS_URL.format(backend=backend),
                headers={"Authorization": f"Bearer {token}"},
                params={"upload_url": query_param},
            ) as response:
                if response.status_code not in [requests.codes.ok]:
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            f"refresh_token: refresh token SAS token failed. {response.text}"
                        )
                    raise requests.HTTPError(f"{response.text}")
                else:
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            "get_token: Get token successfully."
                        )
                    return json.loads(response.text)
        except Exception as err:
            if "progress_bar" in kwargs:
                kwargs["progress_bar"].print(f"get_token: Get token failed. {err}")
            raise err

    def refresh_service_url(self, uri: URL, **kwargs) -> URL:
        """
        :param uri: blob uri, ex: https://seqslabapi97e51storage.blob.core.windows.net/path/...
        :return: complete blob endpoint url with SAS token, ex: https://host/container/path/...?
        st=2021-09-23T02%3A17%3A16Z&se=2021-09-23T03%3A17%3A16Z....
        """
        try:
            data = self.refresh_token(uri.with_query(""))
            sas_token = data["headers"]["Authorization"]
            end_time = URL(sas_token).human_repr().split("&")[1].split("=")[1]
            if arrow.utcnow() > arrow.get(end_time):
                self.refresh_token.cache_clear()
                data = self.refresh_token(uri.with_query(""))
                sas_token = data["headers"]["Authorization"]
            if progress_bar := kwargs.get("progress_bar"):
                progress_bar.print(
                    "refresh_service_url: Refresh service url successfully."
                )
            return URL(uri).with_query(sas_token)
        except LookupError as err:
            if progress_bar := kwargs.get("progress_bar"):
                progress_bar.print(
                    f"refresh_service_url: Refresh service url failed. {err}"
                )
            raise LookupError(err)

    def auth_headers(self):
        headers = super().auth_headers()
        headers.update({"x-ms-version": "2020-08-04"})
        return headers

    @lru_cache(maxsize=16)
    def get_token(self, path: str, **kwargs) -> dict:
        """
        :response payload
        {
          "url": Https URL,
          "region": string,
          "type": string,
          "headers": {
            "Authorization": SAS token
          },
          "alreadyexists": boolean,
          "register_url": Abfss URL
        }
        """
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        workspace = self._workspace
        url = BaseBlob.DRS_SAS_URL.format(name=workspace, backend=backend)
        params = {"name": workspace, "path": path} if path else {"name": workspace}
        try:
            with requests.get(
                url.format(name=workspace),
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            ) as response:
                if response.status_code not in [requests.codes.ok]:
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            f"get_token: Get token failed. {response.text}"
                        )
                    raise requests.HTTPError(f"{response.text}")
                else:
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            "get_token: Get token successfully."
                        )
                    return response.json()
        except Exception as err:
            if "progress_bar" in kwargs:
                kwargs["progress_bar"].print(f"get_token: Get token failed. {err}")
            raise err

    def blob_service_url(self, uri: URL, **kwargs) -> URL:
        """
        :param uri: dst uri, ex: abfss://hostname/path/to/folder or file...
        :return: complete blob endpoint url, ex: https://host/container/path/ or with_query SAS token...
        """

        def https_access_url(get_upload_token, dst: str, **kwargs) -> URL:
            dir_path = (
                os.path.dirname(dst).strip("/")
                if os.path.dirname(dst).strip("/")
                else None
            )
            file = os.path.basename(dst)
            if res := get_upload_token(path=dir_path, **kwargs):
                return URL(f"{res['url']}{file}").with_query(
                    res["headers"]["Authorization"]
                )
            else:
                raise requests.HTTPError(
                    "Get Upload Token Failed: Response payload is incorrect. "
                    "Make sure the Upload Register API version is correct."
                )

        if uri.scheme:
            # refresh token
            parts = uri.parts
            if uri.scheme in ["abfss", "abfs"] and uri.host.endswith(
                ".dfs.core.windows.net"
            ):
                if (
                    len(parts) < 3
                    or not parts[1] == "drs"
                    or not parts[2].startswith("usr_")
                ):
                    raise ValueError(
                        "Enter a valid dst in abfss://container@storageaccount.dfs.core.windows.net"
                        "/path/"
                    )
                else:
                    return https_access_url(
                        self.get_token, "/".join(parts[3:]), **kwargs
                    )

            elif uri.scheme in ["https", "http"] and uri.host.endswith(
                ".blob.core.windows.net"
            ):
                if (
                    len(parts) < 3
                    or not parts[2] == "drs"
                    or not parts[3].startswith("usr_")
                ):
                    raise ValueError(
                        "Enter a valid dst in https://storageaccount.blob.core.windows.net/container/"
                        "/path/"
                    )
                else:
                    return https_access_url(
                        self.get_token, "/".join(parts[4:]), **kwargs
                    )

            else:
                raise ValueError("Enter a valid dst according to the choosing backend.")

        dst = str(uri)
        access_url = https_access_url(self.get_token, dst, **kwargs)
        sas_token = access_url.query_string
        end_time = sas_token.split("&")[1].split("=")[1]
        if arrow.utcnow() > arrow.get(end_time):
            access_url = self.refresh_service_url(access_url, **kwargs)
        return access_url

    @staticmethod
    @njit(nogil=True)
    def _sum_send(results):
        sent = 0
        for res in results:
            if res == 0:
                break
            sent += res
        return sent

    @staticmethod
    def _url_transform(url: URL) -> URL:
        """
        In Azure backend: we store access url with 'abfs or abfss' scheme in mysql database
        https or http -> abfss or abfs
        """
        if url.host.endswith("blob.core.windows.net"):
            host_path = f'{url.parts[1]}@{url.host.split(".")[0]}.dfs.core.windows.net/{"/".join(url.parts[2:])}'
            if url.scheme == "http":
                url = f"abfs://{host_path}"
            elif url.scheme == "https":
                url = f"abfss://{host_path}"
        return URL(url)

    async def upload(
        self,
        uri: URL,
        file: str,
        chunk_size: int = 16 * 1024 * 1024,
        max_concurrency: int = 0,
        md5_check: bool = True,
        *args,
        **kwargs,
    ) -> dict:
        """
        Asynchronous single file uploading
        :return the number of bytes sent.
        """
        file_size = os.stat(file).st_size
        uri = self.blob_service_url(uri=uri, **kwargs)
        position = 0
        block_id_head = '<?xml version="1.0" encoding="utf-8"?> <BlockList>'
        typed_results = List()
        sha256_hash = hashlib.new("sha256")
        with open(file, "rb") as f:
            while position < file_size:
                # split data
                tasks = []
                size = min(max_concurrency * chunk_size, file_size - position)
                end_chunk = size + position
                for pos in range(position, end_chunk, chunk_size):
                    # read file
                    if progress_bar := kwargs.get("progress_bar"):
                        progress_bar.print(f"upload: Read {os.path.basename(file)}")
                    data = f.read(chunk_size)
                    sha256_hash.update(data)
                    base64_message = b64encode(
                        md5(data).hexdigest().encode(), altchars=b"xy"
                    ).decode("ascii")
                    block_id_head += f"<Latest>{base64_message}</Latest>"
                    root = self.get_block_list(uri=uri, **kwargs)
                    block_list = (
                        [child.find("Name").text for child in root.iter("Block")]
                        if root
                        else []
                    )
                    block_size_list = (
                        [child.find("Size").text for child in root.iter("Block")]
                        if root
                        else []
                    )
                    if base64_message in block_list:
                        block_size = int(
                            block_size_list[block_list.index(base64_message)]
                        )
                        if chunk_size == block_size or (end_chunk - pos) == block_size:
                            typed_results.append(block_size)
                            self.upload_success += 1
                            if progress_bar := kwargs.get("progress_bar"):
                                progress_bar.update(self.upload_success)
                                progress_bar.print(
                                    "get_block: Get data block successfully."
                                )
                            continue
                    self.upload_success += 1
                    tasks.append(
                        self.put_block(
                            uri=uri,
                            data=data,
                            position=pos,
                            size=chunk_size,
                            base64_message=base64_message,
                            md5_check=md5_check,
                            **kwargs,
                        )
                    )

                results = await asyncio.gather(*tasks, return_exceptions=True)
                for x in results:
                    if isinstance(x, int):
                        typed_results.append(x)
                    else:
                        typed_results.append(0)
                sent = self._sum_send(typed_results)
                typed_results.clear()

                if sent != size:
                    # request fail and return
                    break

                else:
                    if progress_bar := kwargs.get("progress_bar"):
                        progress_bar.update(self.upload_success)

                position += sent

        block_id = block_id_head + "</BlockList>"
        await self.put_blocklist(uri, block_id, **kwargs)
        if position < file_size:
            raise ValueError([str(x) for x in results if not isinstance(x, int)][0])
        else:
            created_time = datetime.datetime.utcnow()
            workspace = self.workspace(name=self._workspace)
            return {
                "position": position,
                "dst": [str(self._url_transform(uri.with_query("")))],
                "created_time": datetime.datetime.strftime(
                    created_time, "%Y-%m-%dT%H:%M:%S.%f"
                ),
                "region": workspace["location"],
                "access_methods_type": [self._url_transform(uri.with_query("")).scheme],
                "checksums": {"checksum": sha256_hash.hexdigest(), "type": "sha256"},
            }

    @lru_cache(maxsize=16)
    def get_block_list(self, uri: URL, **kwargs) -> iter:
        date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        query_param = {"comp": "blocklist", "blocklisttype": "all"}
        url = uri.update_query(query_param)
        headers = {
            "x-ms-version": "2019-12-12",
            "x-ms-date": date,
        }
        try:
            retry = 5
            while retry:
                retry -= 1
                try:
                    get_block_list = requests.get(
                        url=str(url),
                        headers=headers,
                    )
                    break
                except Exception as err:
                    if progress_bar := kwargs.get("progress_bar"):
                        progress_bar.print(
                            f"Get block list failed, trial ${retry}.(Connection failed with error ${err}.)"
                        )
                        time.sleep(float(1))
            if get_block_list.status_code == 200:
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print("Get block list successfully.")
                return ElementTree.fromstring(get_block_list.text)
            else:
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print("No block list.")
                return
        except Exception as err:
            if progress_bar := kwargs.get("progress_bar"):
                progress_bar.print("Get block list failed.(Connection failed.)")
            raise err

    async def put_block(
        self,
        uri: URL,
        data: open,
        base64_message: str,
        md5_check: bool,
        *args,
        **kwargs,
    ) -> int:
        url = uri.update_query(f"comp=block&blockid={base64_message}")
        date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        headers = {
            "x-ms-version": "2019-12-12",
            "x-ms-date": date,
            "Content-Type": "application/octet-stream",
        }
        length = len(data)
        headers["Content-Length"] = str(length)
        if md5_check:
            headers["Content-MD5"] = b64encode(md5(data).digest()).decode()
        retry = 5
        while retry:
            try:
                with BytesIO(data) as buffer:
                    buffer.seek(0)
                    await self.request(
                        url, "PUT", headers=headers, data=buffer, *args, **kwargs
                    )
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print("Put block successfully.")
                message = length
                break
            except ClientResponseError as err:
                uri = self.refresh_service_url(uri, **kwargs)
                url = uri.update_query(f"comp=block&blockid={base64_message}")
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print(f"Put block failed {err}. retry:{retry}")
                retry -= 1
                if retry == 0:
                    if (
                        "Make sure the value of Authorization header is formed correctly including the signature."
                        in err.message
                    ):
                        message = (
                            f"{uri.with_query('')} is already exist in your storage as different type."
                            f"Please provide a unique upload location."
                        )
                    else:
                        message = err
                pass
            except Exception as err:
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print(f"Put block failed {err}. retry:{retry}")
                retry -= 1
                if retry == 0:
                    message = err
                pass
        return message

    async def put_blocklist(self, uri: URL, block_id: str, *args, **kwargs) -> NoReturn:
        date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        url = uri.update_query("comp=blocklist")
        retry = 5
        while retry:
            retry -= 1
            try:
                await self.request(
                    url,
                    "PUT",
                    headers={
                        "x-ms-version": "2019-12-12",
                        "x-ms-date": date,
                        "Content-Length": str(len(block_id)),
                    },
                    data=block_id,
                    *args,
                    **kwargs,
                )
                break
            except ClientResponseError:
                uri = self.refresh_service_url(uri)
                url = uri.update_query("comp=blocklist")
                if retry == 0:
                    return 0
                pass
            except Exception:
                if retry == 0:
                    return 0
                pass

    async def download(
        self,
        uri: URL,
        file: str,
        chunk_size=64 * 1024 * 1024,
        max_concurrency: int = 1,
        md5_check: bool = True,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> dict:
        file_size = kwargs["size"]
        temp_file = f"{file}.{str(md5(str(uri.with_query('')).encode()).hexdigest())}"
        typed_results = List()
        workspace = self.workspace(name=self._workspace)
        if overwrite:
            if os.path.exists(file):
                os.remove(file)
            elif os.path.exists(temp_file):
                os.remove(temp_file)
            start = 0
        else:
            if os.path.exists(file):
                exist_size = os.stat(file).st_size
                if progress_bar := kwargs.get("progress_bar"):
                    self.download_success += (file_size + chunk_size - 1) // chunk_size
                    progress_bar.update(complete_tasks=self.download_success)
                return {
                    "position": exist_size,
                    "dst": file,
                    "created_time": datetime.datetime.strftime(
                        datetime.datetime.utcnow(), "%Y-%m-%dT%H:%M:%S.%f"
                    ),
                    "region": workspace["location"],
                    "access_methods_type": workspace["resources"][0]["type"],
                    "exception": (
                        ValueError(
                            "Make sure the the file needs to be overwritten or rename the dst name."
                        )
                        if exist_size != file_size
                        else None
                    ),
                }
            elif os.path.exists(temp_file):
                # start with temp
                start = os.stat(temp_file).st_size
                if progress_bar := kwargs.get("progress_bar"):
                    self.download_success += (start + chunk_size - 1) // chunk_size
                    progress_bar.update(complete_tasks=self.download_success)
            else:
                # new file
                start = 0

        tasks = []
        size = min(max_concurrency * chunk_size, file_size - start)
        end_chunk = size + start
        queue = asyncio.Queue(maxsize=1024 * 1024)
        for pos in range(start, end_chunk, chunk_size):
            end = min(pos + chunk_size, file_size) - 1
            queue.put_nowait((pos, end))
        for _ in range(kwargs.get("bandwidth")):
            task = asyncio.create_task(
                self.get_blob(
                    url=uri,
                    pos=queue,
                    file=temp_file,
                    chunk_size=chunk_size,
                    md5_check=md5_check,
                    **kwargs,
                )
            )
            tasks.append(task)
        # start queue in tasks
        await queue.join()
        for task in tasks:
            task.cancel()
        # start cancel tasks
        await asyncio.gather(*tasks, return_exceptions=True)
        exception = None
        for i, x in enumerate(sorted(self.buffer[temp_file], key=lambda x: x["index"])):
            if isinstance(x, Exception):
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print("download: Check block: truncate block.")
                exception = x
                os.truncate(temp_file, start + (i * chunk_size))
                file = temp_file
                break
            elif isinstance(x["exception"], (Exception, ClientResponseError)):
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print("download: Check block: truncate block.")
                exception = x["exception"]
                os.truncate(temp_file, start + (i * chunk_size))
                file = temp_file
                break
            else:
                if progress_bar := kwargs.get("progress_bar"):
                    progress_bar.print("download: Check block: truncate block.")
                typed_results.append(x["length"])
        if typed_results:
            position = self._sum_send(typed_results) + start
            typed_results.clear()
        else:
            position = 0

        os.rename(temp_file, file)
        created_time = datetime.datetime.utcnow()
        return {
            "position": position,
            "dst": file,
            "created_time": datetime.datetime.strftime(
                created_time, "%Y-%m-%dT%H:%M:%S.%f"
            ),
            "region": workspace["location"],
            "access_methods_type": workspace["resources"][0]["type"],
            "exception": exception,
        }

    async def get_blob(
        self, url: URL, file: str, pos: asyncio.queues, **kwargs
    ) -> None:
        while True:
            retry = 3
            start, end = await pos.get()

            while retry:
                try:
                    headers = {
                        "x-ms-version": "2020-04-08",
                        "x-ms-date": datetime.datetime.utcnow().strftime(
                            "%a, %d %b %Y %H:%M:%S GMT"
                        ),
                        "x-ms-range": f"bytes={start}-{end}",
                    }
                    if end - start <= 4 * 1024 * 1024:
                        headers["x-ms-range-get-content-md5"] = str(
                            kwargs.get("md5_check")
                        )
                    o_fd = os.open(file, os.O_WRONLY | os.O_CREAT)
                    os.lseek(o_fd, start, os.SEEK_CUR)
                    response = await self.request(
                        url=url, method="GET", headers=headers, fileobj=o_fd, **kwargs
                    )
                    os.close(o_fd)
                    if progress_bar := kwargs.get("progress_bar"):
                        self.download_success += 1
                        progress_bar.update(complete_tasks=self.download_success)
                    content_md5 = response.attrs.get("x-content-md5")
                    response_content_md5 = response.headers.get("Content-MD5")
                    if response_content_md5:
                        if content_md5 != response_content_md5:
                            raise ValueError(" Chunk data checksum failed")
                    pos.task_done()
                    if self.buffer.get(file):
                        self.buffer[file].append(
                            {
                                "length": end - start + 1,
                                "exception": None,
                                "index": start,
                            }
                        )
                    else:
                        self.buffer[file] = [
                            {
                                "length": end - start + 1,
                                "exception": None,
                                "index": start,
                            }
                        ]
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            "get_blob: Get blob content successfully."
                        )
                    retry = 0
                except ClientResponseError as err:
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            f"get_blob: Get blob content failed. {retry}{err}"
                        )
                    retry -= 1
                    if retry == 0:
                        pos.task_done()
                        if self.buffer.get(file):
                            self.buffer[file].append(
                                {"length": 0, "exception": err, "index": start}
                            )
                        else:
                            self.buffer[file] = [
                                {"length": 0, "exception": err, "index": start}
                            ]
                    url = self.refresh_service_url(url)
                    pass
                except Exception as err:
                    if "progress_bar" in kwargs:
                        kwargs["progress_bar"].print(
                            f"get_blob: Get blob content failed. {retry}{err}"
                        )
                    retry -= 1
                    if retry == 0:
                        pos.task_done()
                        if self.buffer.get(file):
                            self.buffer[file].append(
                                {"length": 0, "exception": err, "index": start}
                            )
                        else:
                            self.buffer[file] = [
                                {"length": 0, "exception": err, "index": start}
                            ]
                    pass

    @lru_cache(maxsize=16)
    async def expand_blob(self, drs_id, **kwargs) -> List[dict] or requests.HTTPError:
        ctx = context.get_context()
        backend = ctx.args.backend
        try:
            token = BaseAuth.get_token().get("tokens").get("access")
            with requests.get(
                BaseBlob.DRS_DOWNLOAD_URL.format(
                    API_HOSTNAME=kwargs.get("self_uri_host", API_HOSTNAME),
                    drs_id=drs_id,
                    backend=backend,
                ),
                headers={"Authorization": f"Bearer {token}"},
                params={"name": kwargs.get("workspace")},
            ) as response:
                if response.status_code not in [requests.codes.ok]:
                    raise requests.HTTPError(f"{json.loads(response.text)}")
                else:
                    return json.loads(response.text)
        except Exception as err:
            raise err
