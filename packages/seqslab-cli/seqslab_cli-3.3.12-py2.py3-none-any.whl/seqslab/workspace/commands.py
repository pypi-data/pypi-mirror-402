# Standard Library
import csv
import errno
import json
import logging
import re
from io import StringIO
from typing import List

from nubia import argument, command, context
from seqslab.exceptions import exception_handler
from tabulate import tabulate
from termcolor import cprint

from .internal.common import get_factory


class BaseWorkspace:
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

    @command(aliases=[])
    @argument(
        "name",
        type=str,
        positional=False,
        description="Specify a workspace name that contains between 1 to 12 lowercase "
        "alphanumeric characters (required).",
    )
    @argument(
        "location",
        type=str,
        choices=[
            "eastus",
            "eastus2",
            "southcentralus",
            "westus2",
            "westus3",
            "australiaeast",
            "southeastasia",
            "northeurope",
            "swedencentral",
            "uksouth",
            "westeurope",
            "centralus",
            "northcentralus",
            "westus",
            "southafricanorth",
            "centralindia",
            "eastasia",
            "japaneast",
            "koreacentral",
            "canadaentral",
            "francecentral",
            "germanywestcentral",
        ],
        positional=False,
        description="Specify the workspace location (required).",
    )
    def create(self, name: str, location: str) -> int:
        """
        Create a workspace.
        """

        def __log(results):
            self._stdout(results=results, output="json")
            msg = "List all workspaces."
            logging.info(msg)

        if re.match(r"^[a-z0-9]*$", name) and len(name) > 12:
            cprint(
                "The name should only contain between 1 to 12 alphanumeric characters."
            )
            return errno.EINVAL

        backend = get_factory().load_resource()
        kwargs = {"name": name, "location": location}
        result = self._create_workspaces(backend, **kwargs)

        if isinstance(result, int):
            return result
        __log(result)
        return 0

    @staticmethod
    @exception_handler
    def _create_workspaces(backend, **kwargs) -> json:
        workspaces = backend.create_workspaces(**kwargs)
        return workspaces

    @command(aliases=[])
    @argument(
        "task_id",
        type=str,
        positional=False,
        description="Create a workspace task ID (required).",
    )
    def status(self, task_id: str) -> int:
        """
        Query workspace creation status using a given task ID.
        """

        def __log(results):
            self._stdout(results=results, output="json")
            msg = "List workspace completely."
            logging.info(msg)

        backend = get_factory().load_resource()
        kwargs = {"task_id": task_id}
        result = self._status(backend, **kwargs)

        if isinstance(result, int):
            return result
        __log(result)
        return 0

    @staticmethod
    @exception_handler
    def _status(backend, **kwargs) -> json:
        workspaces = backend.status(**kwargs)
        return workspaces

    @command(aliases=[])
    @argument(
        "expand",
        type=bool,
        positional=False,
        description="Enable to display the full workspace information. "
        "Otherwise, only display the brief description. Enabling this option is not recommended "
        "because the workspace information might be too long (required).",
    )
    @argument(
        "system",
        type=str,
        positional=False,
        choices=["wes", "drs", "trs"],
        description="Specify the workspace API that you want to use (optional).",
    )
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the stdout format (default = json).",
        choices=["json"],
    )
    def list(self, expand=False, system="wes", output: str = "json") -> int:
        """
        Display a list of available workspaces.
        """

        def __log(results):
            self._stdout(results=results, output=output)
            msg = "List workspace completely."
            logging.info(msg)

        ctx = context.get_context()
        backend = ctx.args.backend
        backend_class = get_factory().load_resource()
        systems = {
            "wes": backend_class.WES_WORKSPACE_URL.format(backend=backend),
            "trs": backend_class.TRS_WORKSPACE_URL.format(backend=backend),
            "drs": backend_class.DRS_WORKSPACE_URL.format(backend=backend),
        }
        kwargs = {"expand": expand, "system": systems[system]}
        result = self._list_workspaces(backend_class, **kwargs)

        if isinstance(result, int):
            return result
        __log(result)
        return 0

    @staticmethod
    @exception_handler
    def _list_workspaces(backend, **kwargs) -> json:
        workspaces = backend.list_workspaces(**kwargs)
        return workspaces


@command
class Workspace(BaseWorkspace):
    """Workspace commands"""

    def __init__(self):
        pass
