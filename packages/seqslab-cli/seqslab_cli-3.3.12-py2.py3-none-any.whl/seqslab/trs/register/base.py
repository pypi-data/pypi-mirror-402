# Standard Library
import json
import logging
import os
from abc import ABC

import requests
from nubia import context
from seqslab.auth.commands import BaseAuth
from seqslab.trs import API_HOSTNAME, __version__
from tenacity import retry, stop_after_attempt, wait_fixed
from yarl import URL

from .template import get_template


class TRSregister(ABC):
    logger = logging.getLogger()

    TRS_TOOL_URL = (
        f"https://{API_HOSTNAME}/trs/{__version__}/tools/?backend={{backend}}"
    )
    TRS_TOOL_URL_SPEC = f"https://{API_HOSTNAME}/trs/{__version__}/tools/{{tool_id}}?backend={{backend}}"
    TRS_TOOLVERSION_URL = f"https://{API_HOSTNAME}/trs/{__version__}/tools/{{tool_id}}/versions/?backend={{backend}}"
    TRS_TOOLVERSION_SPEC_URL = f"https://{API_HOSTNAME}/trs/{__version__}/tools/{{tid}}/versions/{{vid}}/?backend={{backend}}"
    TRS_TOOLFILE_URL = (
        f"https://{API_HOSTNAME}/trs/{__version__}/tools/{{tool_id}}/versions/{{version_id}}/{{"
        f"descriptor_type}}/files/?backend={{backend}}"
    )
    WES_RESOURCES_URL = f"https://{API_HOSTNAME}/wes/v1/service-info/workspaces/{{name}}/resources/?backend={{backend}}"

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_tool(data: dict) -> dict:
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")

        with requests.post(
            url=TRSregister.TRS_TOOL_URL.format(backend=backend),
            headers={"Authorization": f"Bearer {token}"},
            json=data,
        ) as response:
            if response.status_code not in [requests.codes.created]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return response.json()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_version(data: dict, tool_id: str, workspace: str) -> dict:
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")
        with requests.post(
            url=TRSregister.TRS_TOOLVERSION_URL.format(
                tool_id=tool_id, backend=backend
            ),
            headers={"Authorization": f"Bearer {token}"},
            json=data,
            params={"workspace": workspace},
        ) as response:
            if response.status_code not in [requests.codes.created]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return response.json()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_file(
        data: dict, zip_file: str, tool_id: str, version_id: str, descriptor_type: str
    ) -> str:
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")

        files = {
            "file": (
                f"{os.path.basename(zip_file)}",
                open(zip_file, "rb"),
                "application/zip",
            ),
            "file_info": ("", json.dumps(data)),
        }
        workflow_url = TRSregister.TRS_TOOLFILE_URL.format(
            tool_id=tool_id,
            version_id=version_id,
            descriptor_type=descriptor_type,
            backend=backend,
        )
        with requests.post(
            url=workflow_url, headers={"Authorization": f"Bearer {token}"}, files=files
        ) as response:
            if response.status_code not in [requests.codes.created]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return workflow_url.split("?")[0]

    def tool(self, tool_name: str, **kwargs):
        data = get_template("tool").create(
            organization=kwargs.get("organization"),
            toolclass_name=kwargs.get("toolclass_name"),
            toolclass_description=kwargs.get("toolclass_description"),
            tool_name=tool_name,
            description=kwargs.get("description"),
            aliases=kwargs.get("aliases", []),
            checker_url=kwargs.get("checker_url"),
            has_checker=kwargs.get("has_checker"),
            id=kwargs.get("id"),
        )
        return self.post_tool(data=data)

    def version(
        self,
        tool_id: str,
        version_name: str,
        version_id: str,
        descriptor_type: str,
        images: list,
        **kwargs,
    ):
        data = get_template("toolversion").create(
            version_name=version_name,
            version_id=version_id,
            descriptor_type=descriptor_type,
            images=images,
            **kwargs,
        )
        return self.post_version(
            data=data, tool_id=tool_id, workspace=kwargs.get("workspace", None)
        )

    def file(
        self,
        tool_id: str,
        version_id: str,
        descriptor_type: str,
        toolfile_json: dict,
        zip_file: str,
    ):
        return self.post_file(
            data=get_template("toolfile").create(toolfile_json=toolfile_json),
            zip_file=zip_file,
            tool_id=tool_id,
            version_id=version_id,
            descriptor_type=descriptor_type,
        )

    @staticmethod
    def register():
        try:
            return 0
        except Exception as error:
            raise error

    @staticmethod
    def list_tool(page: int, page_size: int):
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")
        url = URL(TRSregister.TRS_TOOL_URL.format(backend=backend)).update_query(
            {"page": page, "page_size": page_size}
        )
        with requests.get(
            url=str(url), headers={"Authorization": f"Bearer {token}"}, stream=True
        ) as response:
            if response.status_code not in [requests.codes.ok]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return response.json()

    @staticmethod
    def list_version(tool_id: str):
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")

        with requests.get(
            url=TRSregister.TRS_TOOLVERSION_URL.format(
                tool_id=tool_id, backend=backend
            ),
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
        ) as response:
            if response.status_code not in [requests.codes.ok]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return response.json()

    @staticmethod
    def get_execs_json(workflow_url: str, download_path: str):
        try:
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")

        url = workflow_url.replace("files", "execs")
        with requests.get(
            url=url, headers={"Authorization": f"Bearer {token}"}, stream=True
        ) as response:
            if response.status_code not in [requests.codes.ok]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )

            with open(download_path, "w") as fd:
                fd.write(response.json().get("content"))

            return response.status_code

    @staticmethod
    def delete_version(tid: str, vid: str):
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")
        with requests.delete(
            url=f"{TRSregister.TRS_TOOLVERSION_SPEC_URL.format(tid=tid, vid=vid, backend=backend)}",
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
        ) as response:
            if response.status_code not in [requests.codes.no_content]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return response.content

    @staticmethod
    def delete_tool(tid: str):
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please signin first!")
        with requests.delete(
            url=f"{TRSregister.TRS_TOOL_URL_SPEC.format(tool_id=tid, backend=backend)}",
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
        ) as response:
            if response.status_code not in [requests.codes.no_content]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )
            return response.content

    @staticmethod
    def get_file(
        tool_id: str, version_id: str, download_path: str, descriptor_type: str
    ):
        try:
            ctx = context.get_context()
            backend = ctx.args.backend
            token = BaseAuth.get_token().get("tokens").get("access")
        except KeyError:
            raise KeyError("No tokens, Please sigin first!")

        url = f"{TRSregister.TRS_TOOLFILE_URL}&expand=true&format=zip"
        with requests.get(
            url=url.format(
                tool_id=tool_id,
                version_id=version_id,
                descriptor_type=descriptor_type,
                backend=backend,
            ),
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
        ) as response:
            if response.status_code not in [requests.codes.ok]:
                raise requests.HTTPError(
                    f"{response.status_code}: {repr(response.text)}"
                )

            with open(download_path, "wb") as fd:
                for chunk in response.iter_content(chunk_size=128):
                    fd.write(chunk)

            return response.status_code
