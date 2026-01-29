# Standard Library
import asyncio
import hashlib
import json
import os
from typing import List, Literal, NamedTuple

from requests import HTTPError
from seqslab.drs.utils.biomimetype import get_mime_type
from seqslab.drs.utils.progressbar import ProgressBarObject
from yarl import URL

from .common import get_factory

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

checksum_type = "sha256"
lock = {}


class CopyResult(NamedTuple):
    name: str
    mime_type: str
    file_type: str
    size: int
    created_time: str
    access_methods: list
    checksums: list
    status: Literal["complete", "partial", "failed"]
    exceptions: str
    description: str = None
    metadata: dict = {}
    tags: list = []
    aliases: list = []
    id: str = None

    @staticmethod
    def checksum(checksum, type):
        return {"checksum": checksum, "type": type}

    @staticmethod
    def access_method(access_methods_type, access_tier, dst, region):
        return {
            "type": access_methods_type,
            "access_url": {"url": dst, "headers": {}},
            "access_tier": access_tier,
            "region": region,
        }

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "mime_type": self.mime_type,
                "file_type": self.file_type,
                "description": self.description,
                "created_time": self.created_time,
                "size": self.size,
                "access_methods": self.access_methods,
                "checksums": self.checksums,
                "metadata": self.metadata,
                "tag": self.tags,
                "aliases": self.aliases,
                "status": self.status,
                "exceptions": self.exceptions,
            }
        )


async def readfile(
    file_path: str, chunk_size: int, sha256_hash, queue: asyncio.Queue
) -> None:
    while True:
        f, position, size = await queue.get()
        f.seek(position)
        content = f.read(size)
        index = int(position / chunk_size)
        while True:
            await asyncio.sleep(1)
            if not index:
                sha256_hash.update(content)
                lock[file_path] = [index]
                break
            elif index - 1 in lock[file_path]:
                sha256_hash.update(content)
                lock[file_path].append(index)
                break
            else:
                pass
        queue.task_done()


async def get_checksum(
    src: str, progress_bar: ProgressBarObject, chunk_size: int = 4 * 1024 * 1024
) -> hex:
    tasks = []
    file_size = os.stat(src).st_size
    queue = asyncio.Queue()
    sha256_hash = hashlib.new(checksum_type)
    f = open(src, mode="rb")
    for start in range(0, file_size, chunk_size):
        size = min(chunk_size, file_size - start)
        queue.put_nowait((f, start, size))
    for _ in range(256):
        progress_bar.print("Checksum calculating")
        task = asyncio.create_task(
            readfile(
                file_path=src,
                chunk_size=chunk_size,
                sha256_hash=sha256_hash,
                queue=queue,
            )
        )
        tasks.append(task)
    await queue.join()
    f.close()
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    return sha256_hash.hexdigest()


def bio_filetype(filename: str) -> str:
    try:
        checker, file_extension = filename.split(".")[-2:]
        if file_extension in [
            "gz",
            "gzip",
            "bai",
            "fai",
            "sa",
            "amb",
            "ann",
            "bwt",
            "pac",
        ]:
            if checker in ["fastq", "fq", "fasta", "fa", "bam", "vcf", "tar"]:
                file_extension = ".".join((checker, file_extension))
    except ValueError:
        file_extension = None
    return file_extension


def argument_setting(files: list, **kwargs) -> tuple:
    multiprocessing = min(len(files), int(kwargs.get("multiprocessing", 1)))
    optargs = {
        "chunk_size": kwargs.get("chunk_size", 16 * 1024 * 1024),
        "md5_check": kwargs.get("md5_check", True),
        "proxy": kwargs.get("proxy"),
    }
    if kwargs.get("concurrency"):
        # memory_usage = max_concurrency * chunk_size * multiprocessing
        optargs["max_concurrency"] = kwargs.get("concurrency")
    else:
        # memory control 512MB per time, not setting too big because of request timeout problem
        max_concurrency = int(
            512 * 1024 * 1024 / optargs["chunk_size"] / multiprocessing
        )
        # handle file too much problem
        if max_concurrency < 1:
            max_concurrency = 1
            multiprocessing = int(512 * 1024 * 1024 / optargs["chunk_size"])
        optargs["max_concurrency"] = max_concurrency
    return multiprocessing, optargs


async def result_setting(status: list, files: List[URL], resp_list: list) -> List[dict]:
    def _create_copyresult(
        sent: int,
        resp: dict,
        mime_type: str,
        file_extension: str,
        checksum: str,
        type: str,
        status: Literal["complete", "partial", "failed"],
    ) -> dict:
        checksums = [CopyResult.checksum(checksum=checksum, type=type)]
        name = os.path.basename(resp["dst"][0]).replace(f".{file_extension}", "")
        access_methods = [
            CopyResult.access_method(
                access_methods_type=(
                    resp["access_methods_type"][i]
                    if resp.get("access_methods_type")
                    else None
                ),
                access_tier="hot",
                dst=dst,
                region=resp["region"],
            )
            for i, dst in enumerate(resp["dst"])
        ]
        return CopyResult(
            name=name,
            mime_type=mime_type,
            file_type=file_extension,
            created_time=resp["created_time"],
            size=sent,
            aliases=[],
            access_methods=access_methods if status == "complete" else None,
            checksums=checksums if status == "complete" else None,
            status=status,
            exceptions=f"{resp.get('exceptions')}" if resp.get("exceptions") else None,
        )._asdict()

    results = []
    for i, sent in enumerate(status):
        file_path = files[i].human_repr()
        size = os.stat(file_path).st_size
        file_extension = bio_filetype(os.path.basename(file_path))
        mime_type = get_mime_type().mime_type(file_extension)
        if sent != 0:
            if sent == size:
                status = "complete"
            else:
                status = "partial"
        else:
            if sent == size:
                status = "complete"
            else:
                status = "failed"
        results.append(
            _create_copyresult(
                sent=sent,
                resp=resp_list[i],
                mime_type=mime_type,
                file_extension=file_extension,
                checksum=resp_list[i]["checksums"]["checksum"],
                type=checksum_type,
                status=status,
            )
        )
    return results


def concat_checksum(checksums: List[str]) -> str or None:
    if len(checksums):
        checksums = [checksum for checksum in checksums if checksum]
        checksums.sort()
        encode_text = "".join(map(str, checksums)).encode()
        checksum = hashlib.sha256(encode_text).hexdigest()
        return checksum
    else:
        return None


def total_blocks(files: [URL], chunk_size: int) -> int:
    blocks = 0
    for file in files:
        block = os.stat(file.path).st_size / chunk_size
        if os.stat(file.path).st_size % chunk_size == 0:
            blocks += int(block)
        else:
            blocks += int(block) + 1
    return blocks


async def result_setting_download(
    resp_list: list, size: list, checksum_bar: ProgressBarObject, **kwargs
) -> dict:
    file_list = []
    total_size = 0
    checksums = []
    checksum_bar.print("result_setting_download: Create json response ")
    template = {
        "src": kwargs.get("self_uri"),
        "checksum_type": checksum_type,
        "files": file_list,
    }
    for i, resp in enumerate(resp_list):
        file_path = resp["dst"]
        rent = resp["position"]
        checksum = None
        if rent != 0:
            if rent == size[i]:
                checksum = await get_checksum(file_path, checksum_bar)
                status = "complete"
            else:
                status = "partial"
        else:
            if rent == size[i]:
                checksum = await get_checksum(file_path, checksum_bar)
                status = "complete"
            else:
                status = "failed"
        total_size += rent
        file = {"dst": file_path, "status": status, "size": rent}
        if resp["exception"]:
            file["errors"] = resp["exception"].__str__()
        template["files"].append(file)
        checksums.append(checksum)
        checksum_bar.update(i + 1)
    if kwargs.get("folder"):
        template["checksum"] = concat_checksum(checksums=checksums)
    else:
        template["checksum"] = checksums[0]
    template["size"] = total_size
    checksum_bar.print("completed checksum calculation.")
    return template


async def file_to_blob(files: List[URL], dst: URL, **kwargs) -> List[dict]:
    """
    Copy local files to the blob storage
    """
    async with get_factory().load_storage(kwargs.get("workspace")) as store:
        multiprocessing, optargs = argument_setting(files, **kwargs)
        progress = 0
        status, resps = [0] * len(files), [0] * len(files)
        blocks = total_blocks(files, kwargs.get("chunk_size"))
        optargs["progress_bar"] = ProgressBarObject(total_tasks=blocks, log=True)
        while progress < len(files):
            tasks = []
            for p in range(
                progress, progress + min(multiprocessing, len(files) - progress)
            ):
                _dst = (
                    URL(
                        os.path.join(str(dst), os.path.basename(files[p].path)),
                        encoded=True,
                    )
                    if str(dst).endswith("/")
                    else dst
                )
                tasks.append(store.upload(_dst, files[p].path, **optargs))
            resp = await asyncio.gather(*tasks, return_exceptions=True)

            for r in resp:
                try:
                    resps[progress] = r
                    if isinstance(r, dict):
                        status[progress] = r["position"]
                    elif isinstance(r, HTTPError):
                        return [
                            {
                                "execptions": f"Token expired:{str(r)}",
                                "status": "failed",
                            }
                        ]
                    else:
                        status[progress] = 0
                    progress += 1
                except RuntimeError:
                    pass

        for i, resp in enumerate(resps):
            if not isinstance(resp, dict):
                resps[i] = {
                    "position": 0,
                    "dst": [f"cloud/{os.path.basename(str(files[i]))}"],
                    "created_time": None,
                    "region": None,
                    "access_methods_type": None,
                    "exceptions": resp,
                    "checksums": {"checksum": None, "type": "None"},
                }
            else:
                continue

        optargs["progress_bar"].print("completed upload.")
        optargs["progress_bar"].end()
        results = await result_setting(status, files, resps)
        return results


async def dir_to_blob(dir: URL, dst: URL, **kwargs) -> List[dict]:
    """
    Copy local directory trees to the cloud storage
    """
    files = []
    relpath = []
    for root, dirlist, filelist in os.walk(dir.human_repr()):
        if filelist:
            for file in filelist:
                if file.startswith("."):
                    # skip file start with '.'
                    print(f"skip {file}")
                    continue
                absolute_path = os.path.join(root, file)
                relative_path = os.path.relpath(absolute_path, dir.human_repr())
                files.append(URL(absolute_path))
                relpath.append(relative_path)

    async with get_factory().load_storage(kwargs.get("workspace")) as store:
        progress: int = 0
        status: list = [0] * len(files)
        resps: list = [0] * len(files)
        multiprocessing, optargs = argument_setting(files, **kwargs)
        blocks = total_blocks(files, kwargs.get("chunk_size"))
        optargs["progress_bar"] = ProgressBarObject(total_tasks=blocks, log=True)

        while progress < len(files):
            tasks = []
            for p in range(
                progress, progress + min(multiprocessing, len(files) - progress)
            ):
                uri = dst.with_path(
                    os.path.join(dst.path.strip("/"), relpath[p].strip("/")),
                    encoded=True,
                )
                tasks.append(store.upload(uri, files[p].path, **optargs))

            resp = await asyncio.gather(*tasks, return_exceptions=True)

            for r in resp:
                try:
                    resps[progress] = r
                    if isinstance(r, dict):
                        status[progress] = r["position"]
                    elif isinstance(r, HTTPError):
                        return [
                            {
                                "execptions": f"Token expired:{str(r)}",
                                "status": "failed",
                            }
                        ]
                    else:
                        status[progress] = 0
                    progress += 1
                except RuntimeError:
                    pass

        for i, resp in enumerate(resps):
            if not isinstance(resp, dict):
                resps[i] = {
                    "position": 0,
                    "dst": [f"cloud/{os.path.basename((files[i].human_repr()))}"],
                    "created_time": None,
                    "region": None,
                    "access_methods_type": None,
                    "exceptions": resp,
                    "checksums": {"checksum": None, "type": "None"},
                }
            else:
                continue

        optargs["progress_bar"].print("completed upload.")
        optargs["progress_bar"].end()
        results = await result_setting(status, files, resps)
        return results


async def blobfile_to_dir(src: URL, dir: URL, **kwargs) -> dict:
    """
    Copy cloud file to the local directory
    """
    async with get_factory().load_storage(kwargs.get("workspace")) as store:
        tasks = []
        if name := kwargs.get("name"):
            file = URL(f"{str(dir)}/{name}")
            os.makedirs(os.path.dirname(str(file)), exist_ok=True)
        else:
            file = os.path.join(str(dir), os.path.basename(src.path))
        file_size = kwargs.get("size")[0]
        chunk_size = kwargs.get("chunk_size")
        max_concurrency = int(file_size / chunk_size)
        if file_size % chunk_size:
            max_concurrency += 1
        optargs = {
            "chunk_size": chunk_size,
            "md5_check": kwargs.get("md5_check", True),
            "proxy": kwargs.get("proxy"),
            "size": file_size,
            "max_concurrency": max_concurrency,
            "bandwidth": kwargs.get("bandwidth"),
            "overwrite": kwargs.get("overwrite"),
        }
        download_bar = ProgressBarObject(total_tasks=max_concurrency, log=True)
        checksum_bar = ProgressBarObject(total_tasks=1, log=True)
        optargs["progress_bar"] = download_bar
        tasks.append(store.download(uri=src, file=str(file), **optargs))
        resps = await asyncio.gather(*tasks, return_exceptions=True)
        download_bar.update(complete_tasks=1)
        download_bar.print("blobfile_to_dir: Download process done.")
        if isinstance(resps[0], Exception):
            return {"files": [{"execptions": resps[0].__str__(), "status": "failed"}]}
        results = await result_setting_download(
            resp_list=resps,
            size=kwargs.get("size"),
            self_uri=kwargs.get("self_uri"),
            checksum_bar=checksum_bar,
        )
        return results


async def blobfile_to_file(src: URL, file: URL, **kwargs) -> dict:
    """
    Copy cloud file to the local file
    """
    async with get_factory().load_storage(kwargs.get("workspace")) as store:
        tasks = []
        file_size = kwargs.get("size")[0]
        chunk_size = kwargs.get("chunk_size")
        max_concurrency = int(file_size / chunk_size)
        if file_size % chunk_size:
            max_concurrency += 1
        optargs = {
            "chunk_size": chunk_size,
            "md5_check": kwargs.get("md5_check", True),
            "proxy": kwargs.get("proxy"),
            "size": file_size,
            "max_concurrency": max_concurrency,
            "bandwidth": kwargs.get("bandwidth"),
            "overwrite": kwargs.get("overwrite"),
            "token": kwargs.get("token"),
        }
        if name := kwargs.get("name"):
            file = URL(f"{str(file)}/{name}")
            os.makedirs(os.path.dirname(str(file)), exist_ok=True)
        download_bar = ProgressBarObject(total_tasks=max_concurrency, log=True)
        checksum_bar = ProgressBarObject(total_tasks=1, log=True)
        optargs["progress_bar"] = download_bar
        tasks.append(store.download(uri=src, file=str(file), **optargs))
        resps = await asyncio.gather(*tasks, return_exceptions=True)
        download_bar.print("blobfile_to_dir: Download process done.")
        if isinstance(resps[0], Exception):
            return {"files": [{"execptions": resps[0].__str__(), "status": "failed"}]}
        results = await result_setting_download(
            resp_list=resps,
            size=kwargs.get("size"),
            self_uri=kwargs.get("self_uri"),
            checksum_bar=checksum_bar,
        )
        return results


async def blobdir_to_dir(srcs: List[URL], dir: URL, **kwargs) -> dict:
    """
    Copy cloud directory tree to the local directory
    """
    async with get_factory().load_storage(kwargs.get("workspace")) as store:
        status = []
        progress = 0
        resp_list = []
        multiprocessing = min(len(srcs), int(kwargs.get("multiprocessing", 1)))
        optargs = {
            "chunk_size": kwargs.get("chunk_size", 16 * 1024 * 1024),
            "md5_check": kwargs.get("md5_check", True),
            "proxy": kwargs.get("proxy"),
            "bandwidth": kwargs.get("bandwidth"),
            "overwrite": kwargs.get("overwrite"),
        }
        total_tasks = sum(
            (size + kwargs["chunk_size"] - 1) // kwargs["chunk_size"]
            for size in kwargs["size"]
        )
        download_bar = ProgressBarObject(total_tasks=total_tasks, log=True)
        checksum_bar = ProgressBarObject(total_tasks=len(srcs), log=True)
        optargs["progress_bar"] = download_bar
        while progress < len(srcs):
            tasks = []
            count = min(multiprocessing, len(srcs) - progress)
            for p in range(progress, progress + count):
                max_concurrency = (
                    int(kwargs.get("size")[p] / kwargs.get("chunk_size")) + 1
                )
                optargs["max_concurrency"] = max_concurrency
                optargs["size"] = kwargs.get("size")[p]
                if access_url := kwargs.get("access_url"):
                    rel_path = os.path.relpath(
                        srcs[p].path, f"/{access_url.user}/{access_url.path}"
                    )
                    file = os.path.join(
                        str(dir), kwargs.get("access_url").parent.name, rel_path
                    )
                else:
                    file = os.path.join(str(dir), kwargs["name"][p])
                os.makedirs(os.path.dirname(file), exist_ok=True)
                tasks.append(store.download(uri=srcs[p], file=file, **optargs))
            resp = await asyncio.gather(*tasks, return_exceptions=True)
            for r in resp:
                try:
                    if isinstance(r["position"], int):
                        status.append(r["position"])
                    else:
                        status.append(0)
                    progress += 1
                    download_bar.update(complete_tasks=progress)
                    download_bar.print("blobdir_to_dir: Download process done.")
                except RuntimeError:
                    pass
                except TypeError or NotADirectoryError:
                    return {"files": [{"execptions": r.__str__(), "status": "failed"}]}

            resp_list.extend(resp)
        results = await result_setting_download(
            resp_list=resp_list,
            size=kwargs.get("size"),
            self_uri=kwargs.get("self_uri"),
            folder=True,
            checksum_bar=checksum_bar,
        )
        return results
