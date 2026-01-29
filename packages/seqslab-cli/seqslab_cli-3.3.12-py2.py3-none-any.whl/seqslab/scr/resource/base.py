# Standard Library
import logging
from functools import lru_cache

import requests
from nubia import context
from seqslab import trs
from seqslab.auth.commands import BaseAuth
from tenacity import retry, stop_after_attempt, wait_fixed


class BaseResource:
    logger = logging.getLogger()
    TRS_BASE_URL = f"https://{trs.API_HOSTNAME}/trs/{trs.__version__}"
    TRS_CR_URL = f"{TRS_BASE_URL}/container-registry/"
    TRS_CR_REPO_URL = f"{TRS_CR_URL}{{registry_id}}/repository/{{repository_name}}"

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def request_wrapper(
        callback,
        url,
        headers,
        status,
        data=None,
        stream=False,
    ) -> requests.Response:
        with callback(url, headers=headers, data=data, stream=stream) as r:
            if r.status_code in status:
                return r
            r.raise_for_status()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    @lru_cache(maxsize=16)
    def list_scr(reload: bool):
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        url = BaseResource.TRS_CR_URL.format(backend=backend) + f"?backend={backend}"
        if reload:
            url += "&force=true"
        r = BaseResource.request_wrapper(
            callback=requests.get,
            url=BaseResource.TRS_CR_URL.format(backend=backend),
            headers={"Authorization": f"Bearer {token}"},
            status=[requests.codes.ok],
        )
        return r.json()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def register_scr(**kwargs):
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        r = BaseResource.request_wrapper(
            callback=requests.post,
            url=BaseResource.TRS_CR_URL.format(backend=backend) + f"?backend={backend}",
            headers={"Authorization": f"Bearer {token}"},
            status=[requests.codes.created],
            data=kwargs,
        )
        return r.json()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    @lru_cache(maxsize=16)
    def get_scr(**kwargs):
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        url = BaseResource.TRS_CR_URL.format(backend=backend) + f"{kwargs.get('id')}/"
        if kwargs.get("reload"):
            url += "?force=true"

        r = BaseResource.request_wrapper(
            callback=requests.get,
            url=url,
            headers={"Authorization": f"Bearer {token}"},
            status=[requests.codes.ok],
        )
        return r.json()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def update_scr(scr_id: str, **kwargs):
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        r = BaseResource.request_wrapper(
            callback=requests.patch,
            url=BaseResource.TRS_CR_URL.format(backend=backend) + f"{scr_id}/",
            headers={"Authorization": f"Bearer {token}"},
            data=kwargs,
            status=[requests.codes.ok],
        )
        return r.json()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def deregister_scr(scr_id: str, **kwargs):
        ctx = context.get_context()
        backend = ctx.args.backend
        token = BaseAuth.get_token().get("tokens").get("access")
        BaseResource.request_wrapper(
            callback=requests.delete,
            url=BaseResource.TRS_CR_URL.format(backend=backend) + f"{scr_id}/",
            headers={"Authorization": f"Bearer {token}"},
            status=[requests.codes.no_content],
        )

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    @lru_cache(maxsize=16)
    def get_repository(**kwargs):
        token = BaseAuth.get_token().get("tokens").get("access")
        url = BaseResource.TRS_CR_REPO_URL.format(
            registry_id=kwargs.get("registry_id"),
            repository_name=kwargs.get("repository_name"),
        )
        if kwargs.get("reload"):
            url += "?force=true"

        r = BaseResource.request_wrapper(
            callback=requests.get,
            url=url,
            headers={"Authorization": f"Bearer {token}"},
            status=[requests.codes.ok],
        )
        return r.json()
