# Standard Library
import logging

import requests
from seqslab.auth.commands import BaseAuth as Auth
from seqslab.exceptions import exception_handler
from seqslab.organization import API_HOSTNAME, __version__
from seqslab.user.resource.base import BaseResource as User
from tenacity import retry, stop_after_attempt, wait_fixed


class BaseResource:
    logger = logging.getLogger()

    MGMT_ORG_URL = f"https://{API_HOSTNAME}/management/{__version__}/organizations/{{organization}}/"

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

    @exception_handler
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def is_global_admin(self, **kwargs) -> bool:
        token = Auth.get_token()
        response = User.get_user(token.get("attrs").get("user_id"))
        return "Global administrator" in response.get("roles")
