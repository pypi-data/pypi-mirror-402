# Standard Library
import asyncio
import csv
import datetime
import errno
import glob
import json
import logging
import os
import re
import sys
from io import StringIO
from typing import List
from urllib.parse import unquote

from jsonpath_ng.ext import parse
from nubia import argument, command, context
from seqslab.color import color_handler
from seqslab.drs.utils.atgxmetadata import AtgxMetaData
from seqslab.drs.utils.progressbar import ProgressBarObject
from seqslab.exceptions import async_exception_handler, exception_handler
from seqslab.runsheet.runsheet import RunSheet
from seqslab.workspace.internal.common import get_factory as get_workspace_factory
from tabulate import tabulate
from termcolor import cprint
from yarl import URL

from . import API_HOSTNAME, __version__
from .api.common import drs_register
from .internal import aiocopy, utils
from .internal.common import get_factory

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


class BaseDatahub:
    DRS_SEARCH_URL = f"https://{API_HOSTNAME}/ga4gh/drs/{__version__}/objects/search/"
    size = {
        "4": 4 * 1024 * 1024,
        "8": 8 * 1024 * 1024,
        "16": 16 * 1024 * 1024,
        "32": 32 * 1024 * 1024,
    }

    @property
    def proxy(self) -> str:
        """web proxy server"""
        return context.get_context().args.proxy

    @staticmethod
    @color_handler
    @exception_handler
    def _upload(src: URL, dst: URL, recursive: bool, **kwargs) -> list:
        # copy from local to cloud
        paths = glob.glob(src.path)
        if 0 == len(paths):
            raise FileNotFoundError("--src Enter a valid src path. ")
        elif 1 == len(paths):
            if os.path.isdir(paths[0]):
                if not recursive:
                    raise OSError("--recursive (-r) is Required.")
                sys.stderr.write(
                    f"{kwargs['green']}"
                    + "Destination Path: "
                    + f"{kwargs['red']}"
                    + f"{str(dst)}\n"
                    + f"{kwargs['yellow']}\0"
                )
                coro = aiocopy.dir_to_blob(URL(*paths), dst, **kwargs)
            else:
                if str(dst).endswith("/"):
                    sys.stderr.write(
                        f"{kwargs['green']}"
                        + "Destination Path: "
                        + f"{kwargs['red']}"
                        + f"{os.path.join(str(dst), os.path.basename(str(src)))} \n"
                        + f"{kwargs['yellow']}\0"
                    )
                else:
                    sys.stderr.write(
                        f"{kwargs['green']}"
                        + "Destination Path: "
                        + f"{kwargs['red']}"
                        + f"{str(dst)} \n"
                        + f"{kwargs['yellow']}\0"
                    )
                coro = aiocopy.file_to_blob([URL(*paths)], dst, **kwargs)
        else:
            sys.stderr.write(
                f"{kwargs['green']}"
                + "Destination Path: "
                + f"{kwargs['red']}"
                + f"cloud://{str(dst)}. \n"
                + f"{kwargs['yellow']}\0"
            )
            files = []
            dirs = []
            for p in paths:
                if os.path.isfile(p):
                    files.append(URL(p))
                else:
                    dirs.append(URL(p))
            if len(dirs) != 0:
                for dir_path in dirs:
                    for root, folderlist, filelist in os.walk(str(dir_path)):
                        if filelist:
                            abs_paths = [
                                URL(os.path.join(root, file)) for file in filelist
                            ]
                            files.extend(abs_paths)
            coro = aiocopy.file_to_blob(files, dst, **kwargs)

        results = asyncio.run(coro)
        for result in results:
            if result["status"] != "complete":
                raise ValueError(json.dumps(results, indent=4))
        return results

    @staticmethod
    def _stdout(results: List[dict], output: str) -> int:
        """
        stdout:: support different format [json, tsv, table]
        """
        if output == "tsv":
            s = StringIO()
            writer = csv.DictWriter(s, fieldnames=list(results[0].keys()))
            writer.writeheader()
            for result in results:
                writer.writerow(result)
            s.seek(0)
            content = s.read().replace(",", "\t")
            cprint(content)
        elif output == "table":
            table_header = list(results[0].keys())
            table_datas = [result.values() for result in results]
            cprint(
                tabulate(
                    tabular_data=table_datas, headers=table_header, tablefmt="pipe"
                )
            )
        else:
            cprint(json.dumps(results, indent=4))
        return 0

    @staticmethod
    def _stdin() -> list:
        payload = sys.stdin.readlines()
        try:
            jsons = json.loads("".join(payload))
            if not isinstance(jsons, list):
                jsons = [jsons]
            return jsons
        except json.JSONDecodeError:
            raise ValueError(
                "Stdin format only supports json. Please read the document and make sure the format is valid."
            )

    @staticmethod
    def _valide_workspace(workspace: str) -> bool:
        ctx = context.get_context()
        backend = ctx.args.backend
        resource = get_workspace_factory().load_resource()
        return resource.validate_workspace(workspace, backend)

    @command(aliases=["copy"])
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "src",
        type=str,
        positional=False,
        description="Specify the source directory, file path, or DRS URL (required).",
    )
    @argument(
        "dst",
        type=str,
        positional=False,
        description="Specify the destination directory, file path, or DRS URL. Paths with leading slashes, leading "
        "backslashes, or dot-only segments are invalid. Additionally, paths should not contain characters other than "
        "[0-9a-zA-Z-._:/]. If not provided, the default is the current Linux epoch timestamp (optional).",
    )
    @argument(
        "recursive",
        type=bool,
        positional=False,
        description="Copy an entire directory tree (optional, default = False).",
        aliases=["r"],
    )
    @argument(
        "concurrency",
        type=int,
        positional=False,
        description="Specify the transmission concurrency in file uploading. The upload bandwidth "
        "can be modified using the formula concurrency * chunk_size * multiprocessing "
        "(default = 64).",
    )
    @argument(
        "multiprocessing",
        type=int,
        positional=False,
        description="Specify the number of files that you want to upload at any given time. (default = 1).",
    )
    @argument(
        "chunk_size",
        type=str,
        positional=False,
        description="Specify the size of each file that you want to upload in mebibyte (MiB). (default = 8MiB).",
        choices=["8", "16"],
    )
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the stdout format (default = json).",
        choices=["json", "table", "tsv"],
    )
    def upload(
        self,
        workspace: str,
        src: str,
        dst: str = f"{str(int(datetime.datetime.now().timestamp()))}/",
        recursive: bool = False,
        output: str = "json",
        concurrency: int = 0,
        multiprocessing: int = 1,
        chunk_size: str = "8",
    ) -> int:
        """
        Upload data from the local file system to a SeqsLab Data Hub cloud service.  This command behaves similarly to gsutil cp command.
        """

        def __log(results: List[dict], output: str):
            self._stdout(results=results, output=output)
            for _, r in enumerate(results):
                msg = "Copy {name} {size}) is {status}".format(
                    name=r.get("name"), size=r.get("size"), status=r.get("status")
                )
                if r.get("status") == "failed":
                    logging.error(msg)
                elif r.get("status") == "partial":
                    logging.error(msg)
                else:
                    logging.info(msg)

        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint(f"Workspace {workspace} not found.", "red")
            return errno.EINVAL

        if dst:
            # Standard Library
            import re

            invalid_patterns = [
                r"(^|/|\\)\.{1,}($|/|\\|$)|^\s*$|^\/$|^\.$|^/|//",  # ex: ., .., ..., ./, ../, .../, ././. etc
                r"[^0-9a-zA-Z\-\._:/]+",
                # ex: Only alphanumeric characters, hyphen, period, colon, and underscore are allowed.
            ]
            for pattern in invalid_patterns:
                if re.search(pattern, dst):
                    logging.error(f"Invalid dst path {dst}")
                    cprint(f"Invalid dst path {dst}.", "red")
                    return errno.EINVAL
        else:
            logging.error("Invalid dst path")
            cprint("Enter a valid dst path.", "red")
            return errno.EINVAL

        if os.path.isdir(src):
            if src.endswith("/"):
                src = URL(f'{str(src).rstrip("/")}', encoded=True)

        result = self._upload(
            src=URL(src, encoded=True),
            dst=URL(dst, encoded=True),
            recursive=recursive,
            workspace=workspace,
            multiprocessing=multiprocessing,
            concurrency=concurrency,
            chunk_size=self.size[chunk_size],
            proxy=self.proxy,
        )
        if isinstance(result, int):
            return result
        __log(result, output)
        return 0

    @command
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "id",
        type=str,
        positional=False,
        description="A DRS object ID (required if there is no self URI).",
    )
    @argument(
        "uri",
        type=URL,
        positional=False,
        description="A DRS self URI (required if there is no DRS ID).",
    )
    @argument(
        "dst",
        type=str,
        positional=False,
        description="Show the destination directory or file path (required).",
    )
    @argument(
        "concurrency",
        type=int,
        positional=False,
        description="Specify the numbers of chunks that can be transferred concurrently. The download bandwidth "
        "can be estimated using the formula concurrency * chunk_size. (optional, default = 120).",
    )
    @argument(
        "multiprocessing",
        type=int,
        positional=False,
        description="Specify the number of files that you want to upload at any given time. (default = 1).",
    )
    @argument(
        "chunk_size",
        type=str,
        positional=False,
        description="Specify the size of chunk in the chunked downloading process. "
        "If the specified size is greater than 4MiB, the md5 hashes are not checked. (optional, default = 4MiB).",
        choices=["4", "8", "16", "32"],
    )
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the output format of the stdout file (optional, default = json).",
        choices=["json", "table", "tsv"],
    )
    @argument(
        "overwrite",
        type=bool,
        positional=False,
        description="Overwrite the existing files (optional, default = false).",
    )
    def download(
        self,
        workspace: str,
        dst: str,
        id: str = None,
        uri: URL = None,
        overwrite: bool = False,
        output: str = "json",
        chunk_size: str = "4",
        concurrency: int = 120,
        multiprocessing: int = 1,
    ) -> int:
        """
        Download the content of a DRS object to a file or directory path.
        """

        def __log(results: List[dict], output: str):
            self._stdout(results=results, output=output)
            for _, r in enumerate(results):
                for _, f in enumerate(r["files"]):
                    msg = "Copy {uri}({size}) is {status}".format(
                        uri=f["dst"], size=f["size"], status=f["status"]
                    )
                    if f["status"] == "failed":
                        logging.error(msg)
                    elif f["status"] == "partial":
                        logging.error(msg)
                    else:
                        logging.info(msg)

        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint(f"Workspace {workspace} not found.", "red")
            return errno.EINVAL

        tasks = []
        kwargs = {}
        if not id:
            if not uri:
                logging.error(
                    "Invalid executions, Enter a valid drs_ids or a valid self_uri."
                )
                cprint(
                    "Invalid executions, Enter a valid drs_ids or a valid self_uri.",
                    "red",
                )
                return errno.EINVAL
            else:
                id = uri.name
                if uri.host:
                    kwargs["self_uri_host"] = uri.host
        else:
            if uri:
                logging.error(
                    "Invalid executions, Enter a valid drs_id or a valid self_uri,"
                    "not both given."
                )
                cprint(
                    "Invalid executions, Enter a valid drs_id or a valid self_uri,"
                    "not both given.",
                    "red",
                )
                return errno.EINVAL

        tasks.append(
            self._download(
                drs_id=id,
                dst=dst,
                workspace=workspace,
                chunk_size=self.size[chunk_size],
                bandwidth=concurrency,
                proxy=self.proxy,
                overwrite=overwrite,
                multiprocessing=multiprocessing,
                **kwargs,
            )
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results, _ = loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        for r in results:
            if isinstance(r.result(), int):
                return r.result()
            result = [r.result()]
        __log(result, output)
        return 0

    @command
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "id",
        type=str,
        positional=False,
        description="A DRS object ID (required if there is no self URI).",
    )
    def share(self, workspace: str, id: str) -> int:
        """
        Generate a share link enabling external users to download the DRS object as a zip archive through web
        browsers. The share link expires either after the first successful download or after a period of three months.
        """

        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        api_backend = drs_register().load_register(workspace)
        r = api_backend.create_download_link(drs_id=id)

        if isinstance(r, int):
            return r
        cprint(r.get("url"), "yellow")
        return 0

    @staticmethod
    @async_exception_handler
    async def _download(drs_id: str, dst: str, **kwargs):
        kwargs["progress_bar"] = ProgressBarObject(total_tasks=1, log=True)
        backend = get_factory().load_storage(kwargs.get("workspace"))
        download_info = await backend.expand_blob(drs_id=drs_id, **kwargs)
        dst = os.path.abspath(os.path.expanduser(dst))
        files = download_info["files"]
        kwargs["size"] = [file["size"] for file in files]
        if len(files) == 1:
            if access_url := download_info.get("access_url"):
                kwargs["access_url"] = URL(access_url)
            else:
                kwargs["name"] = files[0]["name"]

            if os.path.isdir(dst):
                coro = await aiocopy.blobfile_to_dir(
                    src=URL(files[0]["path"]), dir=URL(dst), **kwargs
                )
            else:
                coro = await aiocopy.blobfile_to_file(
                    src=URL(files[0]["path"]), file=URL(dst), **kwargs
                )
        else:
            if access_url := download_info.get("access_url"):
                kwargs["access_url"] = URL(access_url)
            else:
                kwargs["name"] = [file["name"] for file in files]
            coro = await aiocopy.blobdir_to_dir(
                srcs=[URL(file["path"]) for file in files], dir=URL(dst), **kwargs
            )
        for result in coro["files"]:
            if result["status"] != "complete":
                raise ValueError(json.dumps(coro, indent=4))
        return coro

    @command
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "type",
        type=str,
        positional=True,
        description="If you want to register a file as a blob, please choose file. "
        "If you want to register a directory as a blob, please choose dir. "
        "(required).",
        choices=["file", "dir"],
    )
    @argument(
        "name",
        type=str,
        description="Specify the name of the object that you want to register "
        "(optional in stdin mode, otherwise required).",
    )
    @argument(
        "file_type",
        type=str,
        description="Specify the file type of the object that you want to register "
        "(optional in stdin mode, otherwise required). "
        "For example, vcf.gz.",
    )
    @argument(
        "mime_type",
        type=str,
        description="Specify the MIME type of the object that you want to register "
        "(optional stdin mode, otherwise required). "
        "For example, application/json.",
    )
    @argument(
        "description",
        type=str,
        description="Specify the description of the object that you want to register "
        "(optional).",
    )
    @argument(
        "aliases",
        type=List[str],
        description="Specify the aliases of the object that you want to register "
        "(optional).",
    )
    @argument(
        "tags",
        type=List[str],
        positional=False,
        description="Specify the tags that you want to use for the object that you want to register "
        "(optional).",
    )
    @argument(
        "created_time",
        type=str,
        positional=False,
        description="Provide the timestamp of when an object was first created in the storage location. "
        "The time format must be in RFC3339. "
        "If the DRS type is blob, this argument is required (optional in stdin mode). "
        "For example, 2021-09-13 02:54:03.636044+00:00.",
    )
    @argument(
        "updated_time",
        type=str,
        positional=False,
        description="Provide the timestamp of when an object was updated. "
        "The time format must be in RFC3339. "
        "If the DRS type is blob, this argument is required (optional in stdin mode). "
        "For example, 2021-09-13 02:54:03.636044+00:00.",
    )
    @argument(
        "size",
        type=int,
        positional=False,
        description="Specify the size of the object that you want to register. "
        "(optional in stdin mode, otherwise required).",
    )
    @argument(
        "access_methods",
        type=str,
        description="Specify the access methods of the object that you want to register. "
        "(optional in stdin mode, otherwise required)"
        'For example, \'[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
        '"Authorization":authorization}},"access_tier":"hot","region":"westus3"}, ... ]\'',
    )
    @argument(
        "checksum",
        type=str,
        positional=False,
        description="Specify the checksum of the object that you want to register. "
        "The checksum type must be sha256. "
        "If the DRS type is blob, this argument is required "
        "(optional in stdin mode, otherwise required).",
    )
    @argument(
        "checksum_type",
        type=str,
        positional=False,
        description="Specify the type of checksum (optional in stdin mode, otherwise required). "
        "At the moment, only sha256 is supported.",
        choices=["sha256"],
    )
    @argument(
        "metadata",
        type=str,
        positional=False,
        description="Specify a JSON string describing the metadata of the object you want to register "
        "(optional).",
    )
    @argument(
        "stdin",
        type=bool,
        positional=False,
        description="Specify whether or not you want to enable stdin mode (optional). "
        "Selecting stdin prevents you from enabling any of the other options and the json object "
        "must therefore contain all the required keys [name, file_type, mime_type, description, "
        "aliases, tags, created_time, updated_time, size, urls, access_tiers, regions, "
        "Authorizations, checksum, checksum_type, metadata].",
    )
    @argument(
        "deleted_time",
        type=str,
        positional=False,
        description="Specify a date in the format YYYY-MM-DD to set the automatic deletion time for the DRS "
        "object, for example, 2024-01-01 (optional).",
    )
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the output format of the stdout file (optional, default = json).",
        choices=["json", "table", "tsv"],
    )
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify a custom object ID (optional).",
    )
    def register_blob(
        self,
        workspace: str,
        type: str,
        output: str = "json",
        stdin: bool = False,
        **kwargs,
    ) -> int:
        """
        Register a DRS object as a blob.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        def __log(results: List[dict], output: str):
            self._stdout(results=results, output=output)
            for r in results:
                msg = f"Register {r['id']}  is complete."
                logging.info(msg)

        if not stdin:
            if kwargs.get("checksum", None) and kwargs.get("checksum_type", None):
                kwargs["is_integrity"] = True
            elif not kwargs.get("checksum", None) and not kwargs.get(
                "checksum_type", None
            ):
                kwargs["is_integrity"] = False
                cprint(
                    "WARNING: DRS objects registered without checksums will not undergo integrity checks "
                    "during future DRS objects retrieval."
                )
            else:
                cprint(
                    "Give both checksum and checksum_type arguments to register the DRS object with checksum "
                    "for integrity check, otherwise drop both arguments to register the DRS object without "
                    "checksum",
                    "red",
                )
                return errno.EINVAL

        results = self._register_blob(
            drs_type=type, stdin=stdin, workspace=workspace, **kwargs
        )
        if isinstance(results, int):
            return results
        __log(results=results, output=output)
        return 0

    @staticmethod
    @exception_handler
    def _register_blob(
        drs_type: str, stdin: bool, workspace: str, **kwargs
    ) -> List[dict]:
        backend = drs_register().load_register(workspace)
        if stdin:
            payloads = backend.create_payload(
                stdin=BaseDatahub._stdin(), type=drs_type, workspace=workspace, **kwargs
            )
        else:
            if not kwargs["is_integrity"]:
                checksums = []
            else:
                checksums = [
                    {
                        "checksum": kwargs.get("checksum"),
                        "checksum_type": kwargs.get("checksum_type"),
                    }
                ]

            payloads = [
                {
                    "name": kwargs.get("name"),
                    "mime_type": kwargs.get("mime_type"),
                    "file_type": kwargs.get("file_type"),
                    "created_time": kwargs.get("created_time"),
                    "updated_time": (
                        kwargs.get("updated_time")
                        if kwargs.get("updated_time")
                        else kwargs.get("created_time")
                    ),
                    "size": kwargs.get("size"),
                    "access_methods": json.loads(kwargs.get("access_methods")),
                    "checksums": checksums,
                    "description": kwargs.get("description"),
                    "aliases": kwargs.get("aliases"),
                    "metadata": (
                        json.loads(kwargs.get("metadata"))
                        if kwargs.get("metadata")
                        else None
                    ),
                    "tags": kwargs.get("tags"),
                    "id": kwargs.get("id"),
                    "deleted_time": kwargs.get("deleted_time"),
                }
            ]

        results = backend.create_drsobjects(drs_type="blob", payloads=payloads)
        return results

    @command
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "drs_id",
        type=List[str],
        positional=False,
        description="Specify the object ID that will be registered in the bundle (required).",
    )
    @argument(
        "name",
        type=str,
        description="Specify the name of the bundle that you want to register "
        "(must not be in stdin mode, otherwise required).",
    )
    @argument(
        "description",
        type=str,
        description="Specify the description of the bundle that you want to register "
        "(optional).",
    )
    @argument(
        "aliases",
        type=List[str],
        description="Specify the aliases of the bundle that you want to register "
        "(optional).",
    )
    @argument(
        "tags",
        type=List[str],
        positional=False,
        description="Specify the tags that you want to use for the bundle that you want to register "
        "(optional).",
    )
    @argument(
        "metadata",
        type=str,
        positional=False,
        description="Specify a JSON string describing the metadata of the bundle you want to register "
        "(optional).",
    )
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify a custom object ID (optional).",
    )
    @argument(
        "deleted_time",
        type=str,
        positional=False,
        description="Specify a date in the format YYYY-MM-DD to set the automatic deletion time for the DRS "
        "object, for example, 2024-01-01 (optional).",
    )
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the output format of the stdout file (default = json, optional).",
        choices=["json", "table", "tsv"],
    )
    def register_bundle(
        self,
        name: str,
        workspace: str,
        drs_id: List[str],
        output: str = "json",
        **kwargs,
    ):
        """
        Register a DRS object as a bundle.
        """

        def __log(results: List[dict], output: str):
            self._stdout(results=results, output=output)
            for r in results:
                msg = f"{r['id']}  has been registered."
                logging.info(msg)

        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        results = self._register_bundle(
            name=name, drs_ids=drs_id, workspace=workspace, **kwargs
        )
        if isinstance(results, int):
            return results
        __log(results=results, output=output)
        return 0

    @staticmethod
    @exception_handler
    def _register_bundle(
        name: str, drs_ids: List[str], workspace: str, stdin: bool = False, **kwargs
    ) -> List[dict]:
        backend = drs_register().load_register(workspace)
        if stdin:
            raise NotImplementedError("This function is not yet available.")
        else:
            payloads = [
                {
                    "name": name,
                    "mime_type": "application/octet",
                    "file_type": "bundle",
                    "description": kwargs.get("description"),
                    "aliases": kwargs.get("aliases"),
                    "metadata": (
                        json.loads(kwargs.get("metadata"))
                        if kwargs.get("metadata")
                        else None
                    ),
                    "tags": kwargs.get("tags"),
                    "id": kwargs.get("id"),
                    "contents": drs_ids,
                    "deleted_time": kwargs.get("deleted_time"),
                }
            ]

        results = backend.create_drsobjects(drs_type="bundle", payloads=payloads)

        return results

    @command(aliases=["clean"])
    @argument(
        "id",
        type=List[str],
        positional=False,
        description="Specify the IDs of the DRS objects that you want to delete "
        "(optional).",
    )
    @argument(
        "names",
        type=List[str],
        positional=False,
        description="Specify the names of the DRS objects that you want to delete "
        "(optional).",
    )
    @argument(
        "tags",
        type=List[str],
        positional=False,
        description="Specify the labels of the DRS objects that you want to delete "
        "(optional).",
    )
    def delete(
        self,
        id: List[str] = [],
        tags: List[str] = [],
        names: List[str] = [],
    ) -> int:
        """
        Delete DRS objects and the associated files in cloud storage by DRS ID, DRS name, or DRS tag.
        """
        if not id and not names and not tags:
            cprint(
                "Must specify one of the IDs, names or tags to identify "
                "the associated files in cloud storage of DRS objects for deletion",
                "red",
            )
            return errno.ENOENT

        resps = asyncio.run(
            utils.drs_delete(id, names, tags, query_opts="?backend_content=true")
        )
        if isinstance(resps, int):
            cprint(f"Delete with return code {resps}", "red")
            return resps

        for r in resps:
            cprint(r, "yellow")

        return 0

    @command
    @argument(
        "tags",
        type=List[str],
        positional=False,
        description="Locate a DRS object using a list of names " "(optional).",
    )
    @argument(
        "keyword",
        type=str,
        positional=False,
        description="Locate a DRS object with keyword search " "(optional).",
    )
    @argument(
        "page",
        type=int,
        positional=False,
        description="Page index of the return value (optional, default = 1).",
    )
    @argument(
        "page_size",
        type=int,
        positional=False,
        description="Number of record in a page (optional, default = 25).",
    )
    @argument(
        "file_types",
        type=List[str],
        positional=False,
        description="File Type attributes (optional, default = []]).",
    )
    @argument(
        "owner",
        type=bool,
        positional=False,
        description="Whether to return self-own object only (optional, default = False).",
    )
    def search(
        self,
        tags: List[str] = [],
        keyword: str = "",
        page: int = 1,
        page_size: int = 25,
        file_types: List[str] = [],
        owner: bool = False,
    ) -> int:
        """
        Locate DRS objects either by keyword or by tags.
        """
        if not keyword and not tags:
            cprint("Either give keyword or tags to do DRS query", "red")
            return errno.ENOENT
        extra_params = {
            "page": page,
            "page_size": page_size,
            "file_types": file_types,
            "owner": owner,
        }
        result = asyncio.run(utils.drs_keyword_search(keyword, tags, **extra_params))
        cprint(json.dumps(result, indent=4))

        return 0

    @staticmethod
    def find_file_paths(
        file_path: str, file_sig: str, extension: str = "fastq.gz"
    ) -> List[str]:
        return [
            os.path.join(root, f)
            for root, dirs, files in os.walk(file_path)
            for f in files
            if f.find(file_sig) != -1 and f.endswith(extension)
        ]

    @staticmethod
    def create_drs_metadata(hdr_meta, sample_meta):
        md = AtgxMetaData()
        extra_properties = []
        dates = []
        types = []

        platform = "Illumina"
        method = ""
        instrument = ""
        for key in sample_meta:
            if sample_meta[key]:
                extra_properties.append(
                    AtgxMetaData.extra_properties(key, sample_meta[key])
                )

        for key in hdr_meta:
            if hdr_meta[key]:
                extra_properties.append(
                    AtgxMetaData.extra_properties(key, hdr_meta[key])
                )
            if re.search(r"Date", key, re.IGNORECASE):
                dates.append(AtgxMetaData.date_info(hdr_meta[key], "sequencing"))
            if re.search(r"Application", key, re.IGNORECASE):
                method = hdr_meta[key]
            if re.search(r"Instrument Type", key, re.IGNORECASE):
                instrument = hdr_meta[key]
        types.append(
            AtgxMetaData.data_type(
                platform_value=platform, method_value=method, instr_value=instrument
            )
        )

        md.set_dates(dates)
        md.set_types(types)
        md.set_extra_properties(extra_properties)
        return md.get_dictionary()

    @staticmethod
    def match_files_to_runsheet(
        file_path: str,
        run_sheet: RunSheet,
        file_signature_expr: str,
        upload_dst: str,
        base_tgs: str,
        extension: str = "fastq.gz",
    ) -> list:
        """
        Create an upload list based on the Run Sheet and file path information.
        """
        hdr_meta = {
            k.replace(" ", "_"): v for k, v in run_sheet.SampleSheet.Header.items()
        }
        overall_idx = 0
        upload_info = []
        for s in run_sheet.SampleSheet.samples:
            overall_idx += 1
            sample_meta = {k.replace(" ", "_"): v for k, v in s.to_json().items()}
            sample_meta.update({"Order_Overall": str(overall_idx)})
            id_rule = s.get("Drs_ID", None)

            file_signature = BaseDatahub._file_expr(
                file_signature_expr, {**hdr_meta, **sample_meta}
            )
            file_paths = BaseDatahub.find_file_paths(
                file_path, file_signature, extension
            )

            if run_sheet.SampleSheet.is_single_end:
                assert (
                    len(file_paths) == 1
                ), f"sample {str(s.to_json())} does not contain exactly one file path {str(file_paths)}"
                sample_meta["Pair"] = "1"
                upload_info.append(
                    {
                        "src": file_paths[0],
                        "dst": f'{upload_dst}/{file_signature}_{sample_meta.get("Pair")}/',
                        "tags": [
                            f"{base_tgs}{s.get('Run_Name', run_sheet.SampleSheet.Header.Date)}/{s.get('Read1_Label', '')}"
                        ],
                        "metadata": BaseDatahub.create_drs_metadata(
                            hdr_meta, sample_meta
                        ),
                    }
                )
                if id_rule:
                    upload_info[-1]["id"] = BaseDatahub._gen_drs_id(
                        unquote(id_rule), upload_info[-1]["metadata"]
                    ) + extension.replace(".", "_")

            if run_sheet.SampleSheet.is_paired_end:
                assert (
                    len(file_paths) == 2
                ), f"sample {str(s.to_json())} does not contain exactly two file paths {str(file_paths)}"
                file_paths.sort()
                sample_meta["Pair"] = "1"
                upload_info.append(
                    {
                        "src": file_paths[0],
                        "dst": f'{upload_dst}/{file_signature}_{sample_meta.get("Pair")}/',
                        "tags": [
                            f"{base_tgs}{s.get('Run_Name', run_sheet.SampleSheet.Header.Date)}/{s.get('Read1_Label', '')}"
                        ],
                        "metadata": BaseDatahub.create_drs_metadata(
                            hdr_meta, sample_meta
                        ),
                    }
                )

                sample_meta["Pair"] = "2"
                upload_info.append(
                    {
                        "src": file_paths[1],
                        "dst": f'{upload_dst}/{file_signature}_{sample_meta.get("Pair")}/',
                        "tags": [
                            f"{base_tgs}{s.get('Run_Name', run_sheet.SampleSheet.Header.Date)}/{s.get('Read2_Label', '')}"
                        ],
                        "metadata": BaseDatahub.create_drs_metadata(
                            hdr_meta, sample_meta
                        ),
                    }
                )
                if id_rule:
                    upload_info[-1]["id"] = BaseDatahub._gen_drs_id(
                        unquote(id_rule), upload_info[-1]["metadata"]
                    ) + extension.replace(".", "_")
                    upload_info[-2]["id"] = BaseDatahub._gen_drs_id(
                        unquote(id_rule), upload_info[-2]["metadata"]
                    ) + extension.replace(".", "_")

        return upload_info

    @staticmethod
    def _gen_drs_id(rule: str, meta: dict, separator="-", bracket="{}") -> str:
        content = []
        for kw in rule.split(separator):
            try:
                val = parse(kw.strip(bracket)).find(meta)[0].value.replace("/", "-")
                content.append(val)
            except Exception as e:
                cprint(str(e), "red")
                raise RuntimeError(f"Illegal jsonpath expression: {kw.strip(bracket)}")

        return "_".join(filter(None, content))

    @staticmethod
    def _file_expr(rule: str, meta: dict) -> str:
        pattern = r"~{([\w]+)}"
        matches = re.findall(pattern, rule)
        expr = rule
        for m in matches:
            meta_val = meta[m]
            expr = expr.replace(f"~{{{m}}}", str(meta_val))
        return expr

    @command(aliases=["runsheet"])
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "input_dir",
        type=str,
        positional=False,
        description="Specify the input file path (required).",
    )
    @argument(
        "upload_dst",
        type=str,
        positional=False,
        description="Specify the upload destination path (optional).",
    )
    @argument(
        "run_sheet",
        type=str,
        positional=False,
        description="Specify the Run Sheet file path (required).",
    )
    @argument(
        "file_signature",
        type=str,
        positional=False,
        description="Specify the file signature for matching files in the runsheet. "
        "This signature is a string that can include variables from the runsheet header or sample metadata. "
        "Variables should be enclosed in ~{} (e.g., ~{Sample_ID}). "
        "The signature is used to identify files that match each sample in the runsheet. "
        "(optional, default = ~{Sample_ID}).",
        aliases=["fq_sig"],
    )
    @argument(
        "concurrency",
        type=int,
        positional=False,
        description="Specify the transmission concurrency in file uploading. The upload bandwidth "
        "can be modified using the formula concurrency * chunk_size * multiprocessing "
        "(default = 64).",
    )
    @argument(
        "multiprocessing",
        type=int,
        positional=False,
        description="Specify the number of files that you want to upload at any given time. (optional, default = 1).",
    )
    @argument(
        "chunk_size",
        type=str,
        positional=False,
        description="Specify the size of each file that you want to upload in mebibyte (MiB). (default = 8MiB).",
        choices=["8", "16"],
    )
    @argument(
        "seq_run_id",
        type=str,
        positional=False,
        description="Specify a runsheet header field as a sequencer run identifier; the specified value will be "
        "used as a sequencer run specific label for future dataset management (optional).",
    )
    @argument(
        "extension",
        type=str,
        positional=False,
        description="Specify the file extension the runsheet is going to find (optional). (default = "
        "fastq.gz).",
    )
    def upload_runsheet(
        self,
        workspace,
        input_dir: str,
        run_sheet: str,
        upload_dst: str = None,
        file_signature: str = "~{Sample_ID}",
        concurrency: int = 0,
        multiprocessing: int = 1,
        chunk_size: str = "8",
        seq_run_id: str = "",
        extension: str = "fastq.gz",
    ) -> int:
        """
        Upload samples based on the Run Sheet and file path information.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        failed = False
        if not upload_dst:
            upload_dst = int(datetime.datetime.timestamp(datetime.datetime.now()))

        # SampleSheetV2 based RunSheet SeqsLab fields
        seqslab_section = "SeqsLabRunSheet"
        seqslab_format = "SeqsLabColumnFormat"
        seqslab_sep = "#"
        rs = RunSheet(run_sheet, seqslab_section, seqslab_format, seqslab_sep)

        # set base tags
        base_tgs = ""
        try:
            if seq_run_id:
                base_tgs = f"{rs.SampleSheet.Header[seq_run_id]}/"
        except KeyError:
            print(
                f"Given base_label_field not found in SampleSheet Header {seq_run_id}"
            )
            return errno.EINVAL
        upload_payload = BaseDatahub.match_files_to_runsheet(
            input_dir, rs, file_signature, upload_dst, base_tgs, extension
        )
        ret = []
        for payload in upload_payload:
            result = self._upload(
                src=URL(payload.get("src")),
                dst=URL(payload.get("dst")),
                recursive=False,
                workspace=workspace,
                multiprocessing=multiprocessing,
                concurrency=concurrency,
                chunk_size=self.size[chunk_size],
                proxy=self.proxy,
                non_interactive=False,
            )
            if isinstance(result, list):
                r = result[0]
                r["metadata"] = payload.get("metadata")
                r["tags"] = payload.get("tags")
                if payload.get("id"):
                    r["id"] = payload.get("id")
                ret.append(r)
                if r["status"] != "complete":
                    failed = True
            else:
                failed = True
        cprint(json.dumps(ret, indent=4), "yellow")

        # use non-zero return code to indicate upload failed scenario
        if failed:
            return -1
        return 0

    @command(aliases=["patch"])
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "id",
        type=str,
        positional=True,
        description="Specify the DRS object ID (required).",
    )
    @argument(
        "name",
        type=str,
        positional=False,
        description="Specify the DRS object name (optional).",
    )
    @argument(
        "tags",
        type=List[str],
        positional=False,
        description="Specify the DRS object tags (optional).",
    )
    @argument(
        "metadata",
        type=str,
        positional=False,
        description="Specify the DRS object metadata in the format of json string (optional).",
    )
    @argument(
        "checksum",
        type=str,
        positional=False,
        description="Specify the DRS object checksum (required when checksum_type is given).",
    )
    @argument(
        "checksum_type",
        type=str,
        positional=False,
        description="Specify the DRS object checksum type (required when checksum is given).",
        choices=["sha256"],
    )
    @argument(
        "updated_time",
        type=str,
        positional=False,
        description="Specify the timestamp when the DRS object was updated (optional). "
        "The time format must be in RFC3339. "
        "For example, 2021-09-13 02:54:03.636044+00:00.",
    )
    @argument(
        "deleted_time",
        type=str,
        positional=False,
        description="Specify a date in the format YYYY-MM-DD to set the automatic deletion time for the DRS "
        "object, for example, 2024-01-01 (optional).",
    )
    @argument(
        "access_methods",
        type=str,
        positional=False,
        description="Specify the DRS object access_methods in the format of json string (optional)."
        'For example, \'[{"id":320230,"type":"abfss","region":"westus2","access_url":{"headers":{'
        '"Authorization":"st=2025-01-06T060628Z&se=2025-01-09T060628Z00xxx"},'
        '"url":"abfss://org-epa906yha51qwmj@cgmwus232b21storage.dfs.core.windows.net/drs/user_admin'
        "/ref/ffseq/pd4615-sup-0008-file1.rdata\"}}]' ",
    )
    @argument(
        "stdin",
        type=bool,
        positional=False,
        description="Provide a DRS object payload using the stdin mode (optional). "
        "Selecting stdin prevents you from enabling any of "
        "the other options and the json object must therefore contain all the required keys "
        "[name, tags, metadata, checksum, checksum_type, updated_time].",
    )
    def update(self, workspace: str, id: str, stdin: bool = False, **kwargs) -> int:
        """
        Update a DRS object.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        if stdin:
            if len(kwargs) > 0:
                cprint(f"Stdin mode not support {list(kwargs.keys())}")
                return errno.EINVAL
            else:
                kwargs = self._stdin()
                if len(kwargs) > 1:
                    cprint("Enter a valid Json not a list of Json.")
                    return errno.EINVAL
                kwargs = kwargs[0]
        kwargs["workspace"] = workspace

        if metadata := kwargs.get("metadata"):
            try:
                kwargs["metadata"] = json.loads(metadata)
            except Exception as e:
                cprint(f"Provided metadata is not a valid json-string: {e}", "red")
                return errno.EINVAL

        if access_methods := kwargs.get("access_methods"):
            try:
                kwargs["access_methods"] = (
                    json.loads(access_methods)
                    if isinstance(access_methods, str)
                    else access_methods
                )
            except Exception as e:
                cprint(
                    f"Provided access_methods is not a valid json-string: {e}", "red"
                )
                return errno.EINVAL

        def __log(results: dict):
            self._stdout(results=[results], output="json")
            msg = f"Register {results['id']}  is complete."
            logging.info(msg)

        results = self._change(id, **kwargs)
        if isinstance(results, int):
            return results
        __log(results=results)
        return 0

    @staticmethod
    @exception_handler
    def _change(object_id: str, **kwargs) -> dict:
        api_backend = drs_register().load_register(kwargs.get("workspace"))
        return api_backend.change(drs_id=object_id, **kwargs)

    @command(aliases=["retrieve"])
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument("id", type=str, positional=True, description="drs object id.(Required)")
    def get(self, workspace: str, id: str) -> int:
        """
        Get a DRS object.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        def __log(results: dict):
            self._stdout(results=[results], output="json")
            msg = f"Get {results['id']}  completely."
            logging.info(msg)

        results = self._get(id, workspace)
        if isinstance(results, int):
            return results
        __log(results=results)
        return 0

    @staticmethod
    @exception_handler
    def _get(id: str, workspace: str):
        api_backend = drs_register().load_register(workspace)
        return api_backend.get_drs(drs_id=id)

    @exception_handler
    def _patch_add_read_drs(self, add_reads_id: str, workspace: str, tag: str):
        results = self._get(add_reads_id, workspace)
        if isinstance(results, int):
            return results
        cprint(f"Found Add Reads target DRS object {add_reads_id}", color="yellow")
        tags = [item["name"] for item in results["tags"]] + [tag]
        patch_payload = {"tags": tags}
        results = self._change(add_reads_id, **patch_payload)
        if isinstance(results, int):
            return results
        cprint(
            f"Add Reads target DRS object {add_reads_id} patched with tags {tags}",
            color="yellow",
        )
        return add_reads_id

    @command(aliases=["add-reads"])
    @argument(
        "workspace",
        type=str,
        positional=False,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "run_sheet",
        type=str,
        positional=False,
        description="Specify the Run Sheet file path (required).",
    )
    @argument(
        "seq_run_id",
        type=str,
        positional=False,
        description="Specify a runsheet header field as a sequencer run identifier; the specified value will be "
        "used as a sequencer run specific label for future dataset management (optional).",
    )
    def add_reads_runsheet(
        self,
        workspace,
        run_sheet: str,
        seq_run_id: str = "",
    ) -> int:
        """
        Identify and Patch existing DRS object with add-reads runsheet label for runsheet-based run triggering for
        DRS auto-matching
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint("Workspace not found.", "red")
            return errno.EINVAL

        # SampleSheetV2 based RunSheet SeqsLab fields
        seqslab_section = "SeqsLabRunSheet"
        seqslab_format = "SeqsLabColumnFormat"
        seqslab_sep = "#"
        rs = RunSheet(run_sheet, seqslab_section, seqslab_format, seqslab_sep)

        # set base tags
        base_tgs = ""
        try:
            if seq_run_id:
                base_tgs = f"{rs.SampleSheet.Header[seq_run_id]}/"
        except KeyError:
            print(
                f"Given base_label_field not found in SampleSheet Header {seq_run_id}"
            )
            return errno.EINVAL

        add_reads = False
        for sa in rs.SampleSheet.samples:
            if rs.SampleSheet.is_single_end:
                assert not sa.to_json().get("Add_Read2_ID") and not sa.to_json().get(
                    "Add_Read2_Label"
                ), "columns Add_Read2_ID and Add_Read2_Label should be blank for single_end sequencer run"
                if (add_read1_id := sa.to_json().get("Add_Read1_ID")) and (
                    add_read1_label := sa.to_json().get("Add_Read1_Label")
                ):
                    add_reads = True
                    ret = self._patch_add_read_drs(
                        add_read1_id,
                        workspace,
                        f"{base_tgs}{sa.get('Run_Name', rs.SampleSheet.Header.Date)}/"
                        f"{add_read1_label}",
                    )
                    if isinstance(ret, int):
                        return ret
            if rs.SampleSheet.is_paired_end:
                if (add_read1_id := sa.to_json().get("Add_Read1_ID")) and (
                    add_read1_label := sa.to_json().get("Add_Read1_Label")
                ):
                    add_reads = True
                    ret = self._patch_add_read_drs(
                        add_read1_id,
                        workspace,
                        f"{base_tgs}{sa.get('Run_Name', rs.SampleSheet.Header.Date)}/{add_read1_label}",
                    )
                    if isinstance(ret, int):
                        return ret
                if (add_read2_id := sa.to_json().get("Add_Read2_ID")) and (
                    add_read2_label := sa.to_json().get("Add_Read2_Label")
                ):
                    add_reads = True
                    ret = self._patch_add_read_drs(
                        add_read2_id,
                        workspace,
                        f"{base_tgs}{sa.get('Run_Name', rs.SampleSheet.Header.Date)}/{add_read2_label}",
                    )
                    if isinstance(ret, int):
                        return ret

        if not add_reads:
            cprint("No DRS object is patched in this operation", color="yellow")
        return 0


@command
class Datahub(BaseDatahub):
    """Data Hub commands"""

    def __init__(self):
        super().__init__()
