# Standard Library
import json
import logging

import requests
from seqslab import user
from seqslab.auth.commands import BaseAuth
from seqslab.exceptions import exception_handler
from tenacity import retry, stop_after_attempt, wait_fixed


class BaseResource:
    logger = logging.getLogger()

    MGMT_USER_URL = f"https://{user.API_HOSTNAME}/management/{user.__version__}/users/"
    CONSENT_URL = (
        "https://login.microsoftonline.com/{tenant}/adminconsent?"
        "state={user_id}&client_id=b10403db-7700-42c2-996e-116578438579&"
        "redirect_uri={host}/auth/v3/permissions/azure/ "
    )

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def request_wrapper(
        callback,
        url,
        headers,
        status,
        data=None,
        json_data=None,
        stream=False,
    ) -> requests.Response:
        with callback(
            url, headers=headers, json=json_data, data=data, stream=stream
        ) as r:
            if r.status_code in status:
                return r
            else:
                raise requests.HTTPError(json.loads(r.content))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def get_user(self, user_id, **kwargs) -> dict:
        token = BaseAuth.get_token()
        access = token.get("tokens").get("access")
        uid = user_id or token.get("attrs").get("uid")
        r = self.request_wrapper(
            callback=requests.get,
            url=f"{BaseResource.MGMT_USER_URL}{uid}",
            headers={"Authorization": f"Bearer {access}"},
            status=[requests.codes.ok],
        )
        return r.json()

    @exception_handler
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def list_user(self, **kwargs) -> dict:
        token = BaseAuth.get_token().get("tokens").get("access")
        r = self.request_wrapper(
            callback=requests.get,
            url=BaseResource.MGMT_USER_URL,
            headers={"Authorization": f"Bearer {token}"},
            status=[requests.codes.ok],
        )
        return r.json()

    @exception_handler
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def add_user(self, email, roles, active, name, **kwargs) -> dict:
        payload = {
            "username": name,
            "email": email,
            "is_active": active,
            "roles": roles,
        }
        token = BaseAuth.get_token().get("tokens").get("access")
        r = self.request_wrapper(
            callback=requests.post,
            url=BaseResource.MGMT_USER_URL,
            headers={"Authorization": f"Bearer {token}"},
            status=[201],
            json_data=payload,
        )
        return r.json()

    @exception_handler
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def patch_user(self, user_id, payload, **kwargs) -> dict:
        token = BaseAuth.get_token().get("tokens").get("access")
        r = self.request_wrapper(
            callback=requests.patch,
            url="{}{}/".format(BaseResource.MGMT_USER_URL, user_id),
            headers={"Authorization": f"Bearer {token}"},
            status=[200],
            json_data=payload,
        )
        return r.json()

    @exception_handler
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def delete_user(self, user_id, **kwargs) -> requests.Response:
        token = BaseAuth.get_token().get("tokens").get("access")
        r = self.request_wrapper(
            callback=requests.delete,
            url="{}{}/".format(BaseResource.MGMT_USER_URL, user_id),
            headers={"Authorization": f"Bearer {token}"},
            status=[204],
        )
        return r

    @exception_handler
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def is_global_or_org_admin(self, **kwargs) -> bool:
        token = BaseAuth.get_token()
        response = self.get_user(token.get("attrs").get("user_id"))
        roles = [item.get("name") for item in response.get("roles")]
        if "Global administrator" in roles or "Organization administrator" in roles:
            return True

        return False
