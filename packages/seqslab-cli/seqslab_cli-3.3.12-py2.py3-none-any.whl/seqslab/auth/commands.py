#!/usr/bin/env python3
# Standard Library
import errno
import getpass
import json
import logging
import re
from collections import OrderedDict
from typing import Optional
from urllib.parse import quote

import arrow
import jwt
import keyring
import requests
from keyring.errors import PasswordDeleteError
from nubia import argument, command, context
from requests import HTTPError, request
from seqslab import settings as api_settings
from seqslab.auth import __version__, aad_app, azuread
from seqslab.auth.azuread import API_HOSTNAME
from seqslab.auth.utils import get_org, request_wrap
from termcolor import cprint

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


class BaseAuth:
    tokens = OrderedDict()
    ACCESS_TOKEN_METHOD = "POST"
    AUTHORIZATION_URL = f"https://{API_HOSTNAME}/auth/{__version__}/signin/{{backend}}/"
    ACCESS_TOKEN_URL = f"https://{API_HOSTNAME}/auth/{__version__}/token/{{backend}}/"
    REFRESH_TOKEN_URL = f"https://{API_HOSTNAME}/auth/{__version__}/token/refresh/"
    PROFILE_URL = f"https://{API_HOSTNAME}/auth/{__version__}/profile/"
    ORGANIZATION_GET_URL = (
        f"https://{API_HOSTNAME}/management/{__version__}/organizations/{{cus_id}}/"
    )

    def _signin_azure_silent(
        self,
        credential: str,
        assertion: str,
        scope: str,
        backend: str,
        proxy: str = None,
    ) -> dict:
        scopes = azuread.SOCIAL_AUTH_AZURE_SCOPE_APP.get(scope)
        client = aad_app.load_client(
            credential=credential, tenant=self._decode(assertion)["tid"]
        )
        result = client.acquire_token_silent(scopes, account=None)
        if not result:
            logging.info(
                "No suitable token exists in cache. Let's get a new one from AAD."
            )
            result = client.acquire_token_for_client(scopes=scopes)

        if "error" in result:
            raise PermissionError(
                "{}: {}".format(result["error"], result["error_description"])
            )

        result.update({"assertion": assertion, "scope": " ".join(scopes)})
        return request_wrap(
            self.ACCESS_TOKEN_URL.format(backend=backend),
            method=self.ACCESS_TOKEN_METHOD,
            params={"secure": True},
            data=result,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            proxies=proxy,
        ).json()

    def _signin_azure(
        self,
        device_code: bool,
        daemon: bool,
        backend: str,
        organization_id: str,
        proxy: str = None,
    ) -> dict:
        result = None
        token_uri = self.ACCESS_TOKEN_URL.format(backend=backend)
        scopes = azuread.SOCIAL_AUTH_AZURE_SCOPE
        client = aad_app.load_client(tenant=azuread.SOCIAL_AUTH_AZURE_TENANT_ID)
        accounts = client.get_accounts()
        if accounts:
            logging.info(
                "Azure AD account(s) exists in cache and proceed with token cache."
            )

            if 1 == len(accounts):
                chosen = accounts[0]
            else:
                cprint("Pick the account you want to use to proceed:")
                for i, a in enumerate(accounts):
                    cprint(f"({i}) " + a["username"])

                chosen = accounts[int(input("Enter number: "))]

            # Now let's try to find a token in cache for this account
            result = client.acquire_token_silent(scopes=scopes, account=chosen)

        if result is None:
            logging.info(
                "No suitable token exists in cache. You must get a new one from AAD."
            )

            if not device_code:
                # obtain authorization uri
                auth_uri = (
                    request_wrap(
                        self.AUTHORIZATION_URL.format(backend=backend),
                        method=self.ACCESS_TOKEN_METHOD,
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json",
                        },
                        params={"format": "json"},
                        proxies=proxy,
                    )
                    .json()
                    .get("url")
                )

                with azuread.AuthCodeReceiverEx(port=0) as receiver:
                    # hardcode http://localhost here as msal also hardcodes that
                    redirect_uri = f"http://localhost:{receiver.get_port()}"
                    auth_uri = re.sub(
                        r"(redirect_uri=)[^&]+",
                        r"\1" + quote(redirect_uri, safe=""),
                        auth_uri,
                    )
                    auth_uri = re.sub(r"prompt=[^&]+&", "", auth_uri)
                    result = receiver.get_auth_response(
                        auth_uri=auth_uri,
                        timeout=60,
                        success_template="You have signed in with your Microsoft "
                        "account on your device. "
                        "You may now close this window.",
                    )

                    if "error" in result:
                        raise PermissionError(
                            "{}: {}".format(
                                result["error"], result["error_description"]
                            )
                        )

                token_uri = self.AUTHORIZATION_URL.format(backend=backend)
                result.update({"redirect_uri": redirect_uri})
            else:
                flow = client.initiate_device_flow(scopes=scopes)
                if "user_code" not in flow:
                    raise ValueError(
                        "Unable to create device flow. Err: %s"
                        % json.dumps(flow, indent=4)
                    )

                cprint(flow["message"], "red")
                # input("Press Enter after signing in from another device to proceed, CTRL+C to abort.")
                result = client.acquire_token_by_device_flow(flow)
                if "error" in result:
                    raise PermissionError(
                        "{}: {}".format(result["error"], result["error_description"])
                    )
                if organization_id:
                    result.update({"cus_id": organization_id})

        return request_wrap(
            token_uri,
            method=self.ACCESS_TOKEN_METHOD,
            params={"secure": True} if daemon else None,
            data=result,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            proxies=proxy,
        ).json()

    @staticmethod
    def _decode(token) -> dict:
        attrs = jwt.decode(
            token,
            key=api_settings.JWT_VERIFYING_KEY,
            algorithms=[api_settings.JWT_ALGORITHM],
            verify=True,
            options={"verify_aud": False, "verify_exp": False},
        )
        if "exp" not in attrs:
            attrs["exp"] = 0
        return attrs

    @staticmethod
    def get_token() -> Optional[dict]:
        user = getpass.getuser()

        if len(Auth.tokens) == 0:
            # load from Keyring secret service
            refresh = keyring.get_password("net.seqslab.api.tokens.refresh", user)
            access = keyring.get_password("net.seqslab.api.tokens.access", user)
            if not refresh or not access:
                return None

            try:
                attrs = Auth._decode(access)
            except jwt.exceptions.ExpiredSignatureError:
                Auth.tokens.update(
                    {
                        "tokens": {"refresh": refresh, "access": None},
                        "attrs": {"exp": 0},
                    }
                )
            else:
                Auth.tokens.update(
                    {"tokens": {"refresh": refresh, "access": access}, "attrs": attrs}
                )

        if arrow.utcnow() >= arrow.get(Auth.tokens["attrs"]["exp"]):
            # expired, refresh token
            proxy = context.get_context().args.proxy
            with request_wrap(
                Auth.REFRESH_TOKEN_URL,
                method=Auth.ACCESS_TOKEN_METHOD,
                json={"refresh": Auth.tokens["tokens"]["refresh"]},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                proxies=proxy,
            ) as response:
                if response.status_code != requests.codes.ok:
                    Auth.tokens.clear()
                    return None

                result = response.json()
                Auth.tokens["tokens"].update(result)
                Auth.tokens.update({"attrs": Auth._decode(result["access"])})
                keyring.set_password(
                    "net.seqslab.api.tokens.access", user, result["access"]
                )

        return Auth.tokens

    """Authentication command help"""

    @command(
        aliases=["login"],
        help="Authenticate to the platform and obtain API access token.",
    )
    @argument(
        "device_code",
        type=bool,
        positional=False,
        description="Use the device authorization grant flow (optional).",
        aliases=["i"],
    )
    @argument(
        "daemon",
        type=bool,
        positional=False,
        description="Sign in for a long-running, non-interactive daemon process. (optional).",
        aliases=["d"],
    )
    @argument(
        "organization_id",
        type=str,
        positional=False,
        description="The organization id to signin to (optional).  This argument is valid only for device_code flow.",
        aliases=["o"],
    )
    def signin(
        self, device_code: bool = False, daemon: bool = False, organization_id=None
    ) -> int:
        """
        Sign in to the configured authentication backend and obtain API access token.
        """
        if organization_id and not device_code:
            logging.warning("Organization_id is only valid for device code flow")
            cprint("Organization_id is valid only for device cod flow.", "red")
            return errno.EINVAL

        ctx = context.get_context()
        backend = ctx.args.backend
        proxy = ctx.args.proxy
        mname = f"_signin_{backend}"
        if not hasattr(self, mname):
            err = f"Unsupported authentication backend '{backend}'"
            logging.error(err)
            cprint(err, "red")
            return errno.ENODEV

        try:
            method = getattr(self, mname)
            result = method(device_code, daemon, backend, organization_id, proxy)
            # store in keyring secret service
            user = getpass.getuser()

            keyring.set_password(
                "net.seqslab.api.tokens.refresh", user, result["tokens"]["refresh"]
            )
            keyring.set_password(
                "net.seqslab.api.tokens.access", user, result["tokens"]["access"]
            )
            return 0
        except ValueError:
            return errno.EINVAL
        except PermissionError:
            return errno.EACCES
        except ConnectionError:
            return errno.ECONNREFUSED
        except HTTPError as err:
            logging.error(err)
            cprint(err, "red")
            return errno.ECANCELED

    @command(
        aliases=["daemon"],
        help="Authenticate silently to the platform and obtain API access token. "
        "This requires that the SeqsLab API app admin consent has been granted and also the user must "
        "daemon-signin beforehand.",
    )
    @argument(
        "scope",
        type=str,
        positional=False,
        description="Specify the scope of the application permission requested (default = management).",
        choices=["management", "storage"],
    )
    def daemon(self, scope: str = "management") -> int:
        """
        Sign in silently to the configured authentication backend and obtain API access token.
        """
        user = getpass.getuser()
        ctx = context.get_context()
        backend = ctx.args.backend
        proxy = ctx.args.proxy
        mname = f"_signin_{backend}_silent"
        if not hasattr(self, mname):
            err = f"Unsupported authentication backend '{backend}'"
            logging.error(err)
            cprint(err, "red")
            return errno.ENODEV

        if len(Auth.tokens):
            assertion = Auth.tokens["tokens"].get("access")
            credential = Auth.tokens["attrs"].get("scrt")
        else:
            # load from Keyring secret service
            assertion = keyring.get_password("net.seqslab.api.tokens.access", user)
            if not assertion:
                cprint("Not signed in yet")
                return errno.EPERM
            credential = Auth._decode(assertion).get("scrt")

        if not credential:
            cprint("Not signed in for daemon process")
            return errno.EINVAL

        try:
            method = getattr(self, mname)
            result = method(credential, assertion, scope, backend, proxy)
            # store in keyring secret service
            keyring.set_password(
                "net.seqslab.api.tokens.refresh", user, result["tokens"]["refresh"]
            )
            keyring.set_password(
                "net.seqslab.api.tokens.access", user, result["tokens"]["access"]
            )
            org_info = get_org(
                access_token=result["tokens"]["access"],
                cus_id=self._decode(result["tokens"]["access"])["cus_id"],
                proxy=proxy,
            )
            cprint(
                f"Daemon process signin to {org_info['name']}",
                "yellow",
            )
            return 0
        except ValueError:
            return errno.EINVAL
        except PermissionError as err:
            logging.error(err)
            cprint(err, "red")
            return errno.EACCES
        except ConnectionError:
            return errno.ECONNREFUSED
        except HTTPError as err:
            logging.error(err)
            cprint(err, "red")
            return errno.ECANCELED

    @command(aliases=["access-token"])
    def token(self) -> int:
        """
        Print platform access token.
        """
        ctx = context.get_context()
        proxy = ctx.args.proxy
        token = self.get_token()
        if not token:
            cprint("Not signed in yet")
            return errno.EPERM

        org_info = get_org(
            access_token=token["tokens"]["access"],
            cus_id=self._decode(token["tokens"]["access"])["cus_id"],
            proxy=proxy,
        )
        cprint(f"For Organization: {org_info['name']} ({org_info['cus_id']})", "yellow")
        cprint(token["tokens"]["access"], "yellow")
        return 0

    @command(aliases=["logout"])
    def signout(self) -> int:
        """
        Sign out of the session.
        """
        Auth.tokens.clear()
        try:
            user = getpass.getuser()
            keyring.delete_password("net.seqslab.api.tokens.refresh", user)
            keyring.delete_password("net.seqslab.api.tokens.access", user)
            return 0
        except PasswordDeleteError as err:
            cprint(str(err), "red")
            return errno.EAGAIN


@command
class Auth(BaseAuth):
    """Authentication commands"""

    def __init__(self):
        pass
