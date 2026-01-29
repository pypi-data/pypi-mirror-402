# Standard Library
import csv
import json
import logging
from io import StringIO
from typing import List

from nubia import argument, command
from tabulate import tabulate
from termcolor import cprint

from .internal.common import get_factory


class BaseSCR:
    @command(aliases=[])
    @argument(
        "reload",
        type=bool,
        positional=False,
        description="Specify whether to force reload system cache for SCR (optional, default = False).",
    )
    def list(self, reload: bool = False) -> int:
        """
        List all SCR records.
        """

        backend = get_factory().load_resource()
        result = backend.list_scr(reload)

        if isinstance(result, int):
            return result
        self.__log(result)
        return 0

    @command(aliases=[])
    @argument(
        "login_server",
        type=str,
        positional=False,
        description="Specify a container registry login endpoint, e.g. docker.io (required).",
    )
    @argument(
        "username",
        type=str,
        positional=False,
        description="Specify the account for this container registry (required).",
    )
    @argument(
        "password",
        type=str,
        positional=False,
        description="Specify the password for this container registry (required).",
    )
    def register(self, login_server: str, username: str, password: str) -> int:
        """
        Register a container registry to SCR.
        """

        backend = get_factory().load_resource()
        kwargs = {
            "login_server": login_server,
            "username": username,
            "password": password,
        }
        result = backend.register_scr(**kwargs)

        if isinstance(result, int):
            return result
        self.__log(result)
        return 0

    @command(aliases=[])
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify the ID of the SCR (required).",
    )
    @argument(
        "reload",
        type=bool,
        positional=False,
        description="Specify whether to force reload system cache for SCR (optional, default = False).",
    )
    def get(self, id: str, reload: bool = False) -> int:
        """
        Get an SCR record.
        """

        backend = get_factory().load_resource()
        kwargs = {"id": id, "reload": reload}
        result = backend.get_scr(**kwargs)
        if isinstance(result, int):
            return result
        del result["authorization"]

        self.__log(result)
        return 0

    @command(aliases=[])
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify the ID of an SCR (required).",
    )
    @argument(
        "username",
        type=str,
        positional=False,
        description="Specify the account for this container registry (optional).",
    )
    @argument(
        "password",
        type=str,
        positional=False,
        description="Specify the password for this container registry (optional).",
    )
    def update(self, id: str, username: str = "", password: str = "") -> int:
        """
        Update an SCR record.
        """

        backend = get_factory().load_resource()
        kwargs = {}
        if username:
            kwargs["username"] = username
        if password:
            kwargs["password"] = password
        if not kwargs:
            cprint("Nothing to be done due to username and password are not given")
            return 0

        result = backend.update_scr(id, **kwargs)
        if isinstance(result, int):
            return result
        self.__log(result)
        return 0

    @command(aliases=[])
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify the ID of the SCR (required).",
    )
    def deregister(self, id: str) -> int:
        """
        Deregister an SCR record.
        """

        backend = get_factory().load_resource()
        kwargs = {}
        result = backend.deregister_scr(id, **kwargs)

        if isinstance(result, int):
            return result
        self.__log(result)
        return 0

    @command(aliases=[])
    @argument(
        "id",
        type=str,
        positional=False,
        description="Specify the ID of the SCR (required).",
    )
    @argument(
        "repository",
        type=str,
        positional=False,
        description="Specify the repository name (required).",
    )
    @argument(
        "reload",
        type=bool,
        positional=False,
        description="Specify whether to force reload system cache for SCR (optional, default = False).",
    )
    def repository(self, id: str, repository: str, reload: bool = False) -> int:
        """
        Get repository.
        """

        backend = get_factory().load_resource()
        kwargs = {"registry_id": id, "repository_name": repository, "reload": reload}
        result = backend.get_repository(**kwargs)
        if isinstance(result, int):
            return result

        self.__log(result)
        return 0

    def __log(self, results):
        self._stdout(results=results, output="json")
        msg = "List all workspaces."
        logging.info(msg)

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


@command
class scr(BaseSCR):
    """SeqsLab Container Registry SCR commands"""

    def __init__(self):
        pass
