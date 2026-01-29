#!/usr/bin/env python3
# Standard Library
import errno
import getpass
from typing import List

import keyring
import requests
import yarl
from nubia import argument, command, context
from requests import HTTPError
from seqslab.auth.commands import BaseAuth as Auth
from seqslab.auth.utils import get_org
from seqslab.organization.resource.base import BaseResource
from termcolor import cprint

"""
Copyright (C) 2023, Atgenomix Incorporated.

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


class BaseOrg:
    @command
    def list(self, **kwargs) -> int:
        """
        List organizations to which the current user belongs
        """
        ctx = context.get_context()
        backend = ctx.args.backend

        try:
            token = Auth.get_token().get("tokens").get("access")
            organizations = (
                BaseResource.request_wrapper(
                    callback=requests.get,
                    url=Auth.PROFILE_URL.format(backend=backend),
                    headers={"Authorization": f"Bearer {token}"},
                    status=[requests.codes.ok],
                )
                .json()
                .get("organizations")
            )
            for index, org_id in enumerate(organizations):
                values = organizations[org_id]
                cprint(
                    f"{values['name']} ({org_id})",
                    "yellow",
                )
        except HTTPError as e:
            cprint(str(e), "red")
            return errno.EPROTO
        else:
            return 0

    @command
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify an organization ID (required).",
    )
    def switch(self, id, **kwargs) -> int:
        """
        Switch organizations
        """
        ctx = context.get_context()
        backend = ctx.args.backend
        proxy = ctx.args.proxy
        user = getpass.getuser()

        try:
            token = Auth.get_token().get("tokens").get("access")
            resp = BaseResource.request_wrapper(
                callback=requests.get,
                url=f"{Auth.AUTHORIZATION_URL.format(backend=backend)}{id}/",
                headers={"Authorization": f"Bearer {token}"},
                status=[requests.codes.ok],
            ).json()

            keyring.set_password(
                "net.seqslab.api.tokens.refresh", user, resp["tokens"]["refresh"]
            )
            keyring.set_password(
                "net.seqslab.api.tokens.access", user, resp["tokens"]["access"]
            )
            token = resp["tokens"]["access"]

            org_info = get_org(
                access_token=token, cus_id=Auth._decode(token)["cus_id"], proxy=proxy
            )
            cprint(
                f"The organization you are currently signed into: {org_info['name']}.",
                "yellow",
            )
        except HTTPError as e:
            cprint(str(e), "red")
            return errno.EPROTO
        else:
            return 0


@command
class Org(BaseOrg):
    """Organization commands"""

    def __init__(self):
        super().__init__()
