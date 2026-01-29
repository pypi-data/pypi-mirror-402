# Standard Library
from functools import lru_cache

from requests import request
from seqslab.auth import __version__, aad_app, azuread
from seqslab.auth.azuread import API_HOSTNAME

"""
Copyright (C) 2024, Atgenomix Incorporated.

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

ORGANIZATION_GET_URL = (
    f"https://{API_HOSTNAME}/management/{__version__}/organizations/{{cus_id}}/"
)


def request_wrap(url, method, *args, **kwargs):
    response = request(method, url, **kwargs)
    response.raise_for_status()
    return response


@lru_cache(maxsize=16)
def get_org(access_token, cus_id, proxy):
    return request_wrap(
        ORGANIZATION_GET_URL.format(cus_id=cus_id),
        method="GET",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        proxies=proxy,
    ).json()
