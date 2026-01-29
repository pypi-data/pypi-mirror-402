# Standard Library
import errno
import json
import logging
import math
import os
import random
import re
import time
from datetime import datetime
from functools import lru_cache
from typing import List

import pytz
import requests
from nubia import argument, command, context
from requests_toolbelt.multipart.encoder import MultipartEncoder
from seqslab.auth.commands import BaseAuth
from seqslab.exceptions import exception_handler
from seqslab.runsheet.runsheet import Run, RunSheet
from seqslab.trs.register.common import trs_register
from seqslab.workspace.internal.common import get_factory as get_workspace_factory
from tenacity import retry, stop_after_attempt, wait_fixed
from termcolor import cprint
from tzlocal import get_localzone

from . import API_HOSTNAME, __version__
from .internal import parameters
from .resource.common import get_factory

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


class BaseJobs:
    WES_PARAMETERS_URL = (
        f"https://{API_HOSTNAME}/wes/{__version__}/schedules/parameters/"
    )
    OPERATOR_PIPELINE_URL = (
        f"https://{API_HOSTNAME}/wes/{__version__}/operator-pipelines/{{pipeline_id}}/"
    )

    @staticmethod
    def _valide_workspace(workspace: str) -> bool:
        ctx = context.get_context()
        backend = ctx.args.backend
        resource = get_workspace_factory().load_resource()
        return resource.validate_workspace(workspace, backend)

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    @lru_cache(maxsize=16)
    def parameter(primary_descriptor: str, zip_file: str):
        token = BaseAuth.get_token().get("tokens").get("access")
        files = {
            "file": (
                f"{os.path.basename(zip_file)}",
                open(zip_file, "rb"),
                "application/zip",
            ),
            "PRIMARY_DESCRIPTOR": ("", primary_descriptor),
        }
        with requests.patch(
            url=BaseJobs.WES_PARAMETERS_URL,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            if response.status_code not in [requests.codes.ok]:
                raise requests.HTTPError(response.text)
            return json.loads(response.content)

    @property
    def proxy(self) -> str:
        """web proxy server"""
        return context.get_context().args.proxy

    @command
    @argument(
        "working_dir",
        type=str,
        positional=False,
        description="Specify the working directory path that contains request.json.  All files end with "
        "request.json will be identify and execute (optional).",
    )
    @argument(
        "request_path",
        type=str,
        positional=False,
        description="Specify the request.json file to run (optional).",
    )
    @argument(
        "response_path",
        type=str,
        positional=False,
        description="Specify the path of response.json in relation to the working directory (optional).",
    )
    @argument(
        "workspace",
        type=str,
        description="Specify the workspace based on the signed in account (required).",
    )
    def run(
        self,
        workspace: str,
        working_dir: str = "",
        request_path: str = "",
        response_path: str = "response.json",
    ) -> int:
        """
        Run a workflow by calling seqslab-api/wes/runs API.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint(f"Workspace {workspace} not found.", "red")
            return errno.EINVAL

        reqs = []
        if working_dir:
            if not os.path.isdir(working_dir):
                logging.error("working dir is not a directory")
                cprint("working dir is not a directory", "red")
                return errno.EINVAL
            else:
                reqs += [
                    os.path.join(working_dir, f)
                    for f in os.listdir(working_dir)
                    if os.path.isfile(os.path.join(working_dir, f))
                    and f.endswith("request.json")
                ]

        if request_path:
            if not os.path.isfile(request_path):
                logging.error("request_path is not a file")
                cprint("request_path is not a file", "red")
                return errno.EINVAL
            else:
                reqs += [request_path]

        if not len(reqs):
            cprint("no request.json are found", "yellow")
            return errno.EINVAL

        run_list = []

        for value in enumerate(reqs):
            # add random delay, based on reqs.index for run submission to avoid overloading SeqsLab-API server
            if value[0]:
                floor = math.log((value[0] + 1), 2)
                step = (value[0] + 1) * 0.1
                time.sleep(random.uniform(floor, floor + step))

            try:
                with open(value[1], "r") as f:
                    request = json.load(f)
            except json.decoder.JSONDecodeError as e:
                cprint(f"given request not in json format - {e}", "red")

            mp = MultipartEncoder(
                fields={
                    "name": request.get("name"),
                    "workflow_type": request.get("workflow_type"),
                    "workflow_type_version": request.get("workflow_type_version"),
                    "workflow_url": request.get("workflow_url"),
                    "workflow_params": json.dumps(request.get("workflow_params")),
                    "workflow_backend_params": json.dumps(
                        request.get("workflow_backend_params")
                    ),
                    "tags": request.get("tags"),
                }
            )
            resource = get_factory().load_resource()
            ret = resource.sync_run_jobs(
                data=mp,
                headers={"Content-Type": mp.content_type, "X-Retry-Policy": "robust"},
                run_request_id=None,
                run_name=request.get("name"),
            )
            res = json.loads(ret.content.decode("utf-8"))
            res["run_name"] = request.get("name")
            run_list.append(res)
            cprint(f"{res}", "yellow")

        with open(os.path.join(working_dir, response_path), "w") as f:
            json.dump(run_list, f, indent=4)

        return 0

    @command
    @argument(
        "request_path",
        type=str,
        positional=False,
        description="Specify the request.json file to run (required).",
    )
    @argument(
        "workspace",
        type=str,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "date",
        type=str,
        positional=False,
        aliases=["d"],
        description="Specify the schedule date, in the format of YYYY-MM-DD (required).",
    )
    @argument(
        "time",
        type=str,
        positional=False,
        aliases=["t"],
        description="Specify the schedule time, in the format of HH-MM (required).",
    )
    @argument(
        "time_zone",
        type=str,
        choices=["UTC", "LOCAL"],
        positional=False,
        aliases=["z"],
        description="Specify the time zone for the provided date and time. If 'LOCAL' is selected, the date and time "
        "will be interpreted according to the operating system's time zone. (optional, default = UTC).",
    )
    @argument(
        "recurrence",
        type=str,
        positional=False,
        aliases=["r"],
        choices=["Once", "Hourly", "Daily", "Weekly", "Monthly"],
        description="Specify the schedule recurrence (optional, default = Once).",
    )
    def schedule(
        self,
        request_path: str,
        workspace: str,
        date: str,
        time: str,
        time_zone: str = "UTC",
        recurrence: str = "Once",
    ) -> int:
        """
        Schedule a WES run with given date, time, and recurrence.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint(f"Workspace {workspace} not found.", "red")
            return errno.EINVAL

        if not os.path.isfile(request_path):
            cprint("request_path is not a file", "red")
            return errno.EINVAL
        else:
            try:
                with open(request_path, "r") as f:
                    req = json.load(f)
            except json.decoder.JSONDecodeError as e:
                cprint(f"given request not in json format - {e}", "red")
                return errno.EINVAL

        if not self._is_valid_time(date, "%Y-%m-%d"):
            cprint(f"date {date} not in YYYY-MM-DD format", "red")
            return errno.EINVAL

        if not self._is_valid_time(time, "%H:%M"):
            cprint(f"time {time} not in HH-MM format", "red")
            return errno.EINVAL

        time_f = f"{date} {time}"

        if time_zone == "LOCAL":
            time_f, msg = self._to_utc(time_f)
            if not time_f:
                cprint(f"timezone transform failed {msg}", "red")
                return errno.EINVAL

        payloads = {
            "schedule": {"schedule_type": recurrence[0], "next_run": time_f},
            "request": req,
        }

        resource = get_factory().load_resource()
        ret = resource.schedule_run(
            data=payloads,
        ).json()
        cprint(
            f"wes_schedule_id: {ret['id']}; schedule_details: {str(ret['schedule'])}",
            "yellow",
        )
        return 0

    @staticmethod
    def _is_valid_time(time_str: str, time_format: str):
        try:
            datetime.strptime(time_str, time_format)
            return True
        except ValueError:
            return False

    @staticmethod
    def _to_utc(local_t: str):
        try:
            local_timezone = pytz.timezone(get_localzone().key)
            utc_t = (
                local_timezone.localize(datetime.strptime(local_t, "%Y-%m-%d %H:%M"))
                .astimezone(pytz.utc)
                .strftime("%Y-%m-%d %H:%M")
            )
            return utc_t, None
        except Exception as e:
            return None, str(e)

    @command(aliases=["state"])
    @argument(
        "run_id",
        type=str,
        positional=False,
        description="Specify a previously executed WES run ID (required).",
    )
    def run_state(self, run_id: str) -> int:
        """
        Get WES run information based on run ID.
        """
        result = get_factory().load_resource().get_run_status(run_id)
        cprint(json.dumps(result), "yellow")

        return 0

    @command(aliases=["runsheet"])
    @argument(
        "working_dir",
        type=str,
        description="Specify the absolute output directory for generated request.json for WES runs (required). ",
        aliases=["o"],
    )
    @argument(
        "run_sheet",
        type=str,
        description="Specify the absolute output path for Run Sheet (required). ",
        aliases=["r"],
    )
    @argument(
        "integrity",
        type=bool,
        description="Specify whether to enable data and runtime integrity check for the workflow engine "
        "(optional, default = False).",
    )
    @argument(
        "trust",
        type=bool,
        description="Specify whether to enable content trust for container runtime "
        "(optional, default = False).",
    )
    @argument(
        "workspace",
        type=str,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "kernel_version",
        type=str,
        description="Specify the SeqsLab kernel version (optional).",
    )
    @argument(
        "fastq_signature",
        type=str,
        positional=False,
        description="Define a fastq path matching pattern using ~{} wrapping syntax for Runsheet column "
        "names. For example, ~{Sample_Name}_S~{Sample_ID} matches `NA12878_S1.fastq.gz` with "
        "Sample_Name as `NA12878` and Sample_ID as `1` (optional, defaulting to ~{Sample_ID}).",
        aliases=["fq_sig"],
    )
    @argument(
        "token_lifetime",
        type=int,
        positional=False,
        description="Specify the duration, in hours, for the SeqsLab API token lifespan for this run (optional, "
        "default = 2).",
    )
    @argument(
        "seq_run_id",
        type=str,
        positional=False,
        description="Specify a runsheet header field as a sequencer run identifier; the specified value will be "
        "used as a sequencer run specific label for future jobs management (optional).",
    )
    def request_runsheet(
        self,
        working_dir: str,
        run_sheet: str,
        workspace: str,
        integrity: bool = False,
        trust: bool = False,
        kernel_version: str = "",
        fastq_signature: str = "~{Sample_ID}",
        token_lifetime: int = 2,
        seq_run_id: str = "",
    ):
        """
        Parse run_sheet.csv and create a request.json file for each WES run.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint(f"Workspace {workspace} not found.", "red")
            return errno.EINVAL

        if not os.path.isdir(working_dir):
            logging.error("working dir is not a directory")
            cprint("working dir is not a directory", "red")
            return errno.EINVAL
        try:
            seqslab_section = "SeqsLabRunSheet"
            seqslab_format = "SeqsLabColumnFormat"
            seqslab_sep = "#"
            run_sheet = RunSheet(
                run_sheet, seqslab_section, seqslab_format, seqslab_sep
            )
        except ValueError as e:
            cprint(e, "red")
            return -1

        # set base tags
        base_tgs = ""
        try:
            if seq_run_id:
                base_tgs = run_sheet.SampleSheet.Header[seq_run_id]
        except KeyError:
            print(f"Given base_label_field not found {seq_run_id}")
            return errno.EINVAL

        for run in run_sheet.runs:
            self._runs_routine(
                run=run,
                working_dir=working_dir,
                workspace=workspace,
                execs=None,
                integrity=integrity,
                trust=trust,
                is_runsheet_template=True,
                is_single_end=run_sheet.SampleSheet.is_single_end,
                kernel_version=kernel_version,
                fq_signature=fastq_signature,
                token_lifetime=token_lifetime,
                tags=[f"{base_tgs}/{run.run_name}" if base_tgs else run.run_name],
            )
        return 0

    def _runs_routine(
        self,
        run: Run,
        working_dir: str,
        workspace: str,
        execs: str = None,
        integrity: bool = False,
        trust: bool = False,
        kernel_version: str = "",
        is_runsheet_template: bool = False,
        is_single_end: bool = False,
        fq_signature: str = "~{Sample_ID}",
        token_lifetime: int = 2,
        tags: List[str] = [],
    ):
        def label_field_validation(label):
            message = (
                f"label Name ({label}) can only contain alphanumeric characters "
                f"and other special characters (#_`~!@%^*()+-. :)."
            )
            regex = re.compile(r"(\w|[#_`~!@%^*()+-. :])+")
            if not regex.fullmatch(label):
                raise ValueError(message)

        for sample in run.samples:
            lbs = [sample.run_name, sample.Read1_Label]
            if sample.Read2_Label:
                lbs.append(sample.Read2_Label)
            for lbl in lbs:
                for item in lbl.split("/"):
                    label_field_validation(item)

        pattern = r"[# `~!@%^*()+.:/]"
        rpath = re.sub(pattern, "_", run.run_name)
        execs_path = f"{working_dir}/{rpath}-execs.json"
        request_path = f"{working_dir}/{rpath}-request.json"
        wf_info = run.workflow_url.split("versions")[1].strip("/").split("/")

        resource = get_factory().load_resource()
        if run.run_schedule_id:
            req = resource.get_schedule(run.run_schedule_id).get("request")
            params = req.get("workflow_params")
            backend_params = req.get("workflow_backend_params")
        else:

            if not execs:
                trs_register().load_resource().get_execs_json(
                    workflow_url=run.workflow_url, download_path=execs_path
                )
            else:
                execs_path = f"{working_dir}/{execs}"

            ops = resource.list_operator_pipelines(page=1, page_size=1000)["results"]
            opp_w_args = [
                op["id"]
                for op in ops
                for operator in op["operators"]
                if isinstance(operator, dict) and operator.get("arguments")
            ]
            params = parameters.workflow_params(
                execs_path,
                opp_w_args,
            )
            backend_params = parameters.workflow_backend_params(
                execs_path,
                workspace,
                run.runtimes,
                integrity,
                trust,
                kernel_version,
                token_lifetime,
            )

        if is_runsheet_template:
            params = parameters.runsheet_rendering(
                params, run, fq_signature, is_single_end
            )

        if not isinstance(params, dict):
            raise Exception(
                f"Unable to generate workflow_params based on given exec_path, with error code {params}"
            )

        request = {
            "name": run.run_name,
            "workflow_params": params,
            "workflow_backend_params": backend_params,
            "workflow_url": run.workflow_url,
            "workflow_type_version": "1.0",
            "workflow_type": wf_info[1],
            "tags": ",".join(tags),
        }
        with open(request_path, "w") as f:
            json.dump(request, f, indent=4)

    @command
    @argument(
        "run_name",
        type=str,
        description="Define the run name for a single run (required). ",
        aliases=["name"],
    )
    @argument(
        "working_dir",
        type=str,
        description="Specify the absolute output directory for generated request.json (required). ",
        aliases=["dir"],
    )
    @argument(
        "workflow_url",
        type=str,
        description="Specify a workflow URL for a run. "
        "For example, https://api.seqslab.net/trs/v2/tools/trs_id/versions/1.0/WDL/files/ (required). ",
        aliases=["url"],
    )
    @argument(
        "execs",
        type=str,
        description="Specify the execs.json needed to create a WES request.  If not given, the command will "
        "get the execs.json from the TRS object specified by the workflow_url "
        "(optional, default = None).",
    )
    @argument(
        "runtimes",
        type=str,
        description="String of key-value pairs using : as a separator, indicating the execution runtimes for each task "
        "or workflow defined in workflow-url. For example, Main=m4-cluster:Main>Fq2Bam=m4-8xcluster. To "
        "list tasks/workflows for a given workflow, use the execs command. To find available runtime "
        "options, use the request runtimes_options command. (Optional, defaults to None, which runs the "
        "entire workflow using m4-cluster.)",
    )
    @argument(
        "integrity",
        type=bool,
        description="Specify whether to enable data and runtime integrity check for the workflow engine "
        "(optional, default = False).",
    )
    @argument(
        "trust",
        type=bool,
        description="Specify whether to enable content trust for container runtime "
        "(optional, default = False).",
    )
    @argument(
        "workspace",
        type=str,
        description="Specify the workspace based on the signed in account (required).",
    )
    @argument(
        "kernel_version",
        type=str,
        description="Specify the SeqsLab kernel version (optional, default = None).",
    )
    @argument(
        "token_lifetime",
        type=int,
        positional=False,
        description="Specify the duration, in hours, for the SeqsLab API token lifespan for this run (optional, "
        "default = 2).",
    )
    @argument(
        "labels",
        type=List[str],
        positional=False,
        description="Specify labels for the run; multiple labels can be given with whitespaces as separators ("
        "optional).",
    )
    def request(
        self,
        run_name: str,
        working_dir: str,
        workflow_url: str,
        workspace: str,
        execs=None,
        runtimes=None,
        integrity=False,
        trust=False,
        kernel_version="",
        token_lifetime=2,
        labels: List[str] = [],
    ):
        """
        Create WES run request.
        """
        if not self._valide_workspace(workspace):
            logging.error("Workspace not found")
            cprint(f"Workspace {workspace} not found.", "red")
            return errno.EINVAL

        if not os.path.isdir(working_dir):
            logging.error("working dir is not a directory")
            cprint("working dir is not a directory", "red")
            return errno.EINVAL
        try:
            single_run = Run(list(), run_name, workflow_url, runtimes)
        except ValueError as e:
            cprint(e, "red")
            return -1
        self._runs_routine(
            run=single_run,
            working_dir=working_dir,
            workspace=workspace,
            execs=execs,
            integrity=integrity,
            trust=trust,
            kernel_version=kernel_version,
            token_lifetime=token_lifetime,
            tags=labels,
        )
        return 0

    @command
    @argument(
        "run_id",
        type=str,
        positional=False,
        description="Specify a previously executed WES run ID (required).",
    )
    def get(self, run_id: str) -> int:
        """
        Get WES run information based on run ID.
        """
        try:
            result = get_factory().load_resource().get_run_id(run_id)
            cprint(json.dumps(result, indent=4), "yellow")
        except requests.HTTPError:
            cprint(f"given run_id {run_id} is not valid.", "red")
            return -1

        return 0

    @exception_handler
    def _get_run_id(self, rerun_id):
        return get_factory().load_resource().get_run_id(rerun_id)

    @command
    @argument(
        "rerun_id",
        type=str,
        positional=False,
        description="Specify the run_id that is going to be rerun (required).",
    )
    def rerun(self, rerun_id: str) -> int:
        """
        Rerun an existing run by calling the seqslab-api/wes/runs API.
        """
        run_obj = self._get_run_id(rerun_id=rerun_id)
        if isinstance(run_obj, int):
            return run_obj

        mp = MultipartEncoder(fields={})
        resource = get_factory().load_resource()
        ret = resource.sync_run_jobs(
            data=mp,
            headers={"Content-Type": mp.content_type, "X-Retry-Policy": "robust"},
            run_request_id=None,
            run_name=None,
            rerun_id=rerun_id,
        )
        res = json.loads(ret.content.decode("utf-8"))
        cprint(f"{res}", "yellow")
        return 0

    @command
    @argument(
        "run_id",
        type=str,
        positional=False,
        description="Specify the run_id that is going to be cancelled (required).",
    )
    def cancel(self, run_id: str) -> int:
        """
        Cancel WES run based on run ID.
        """
        try:
            result = get_factory().load_resource().cancel_run(run_id)
            cprint(json.dumps(result, indent=4), "yellow")
        except requests.HTTPError as e:
            cprint(f"Fail to cancel Job {run_id} - '{str(e)}'.", "red")
            return -1
        return 0

    @command
    @argument(
        "run_id",
        type=str,
        positional=False,
        description="Specify the run_id that you are trying to validate (required).",
    )
    @argument(
        "output_path",
        type=str,
        description="Specify the absolute output path for keeping the WES run detail_config.json. If not given, "
        "the command will return the detail_config.json to stdout (optional). ",
    )
    def detail(self, run_id: str, output_path: str = "") -> int:
        """
        Get WES run detail_config.json with a run ID.
        """
        try:
            result = get_factory().load_resource().wes_files(run_id)
            if output_path:
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=4)
            else:
                cprint(json.dumps(result, indent=4), "yellow")
        except requests.HTTPError:
            cprint(f"given run_id {run_id} is not valid.", "red")
            return -1

        return 0

    @command(aliases=["rt"])
    @argument(
        "page",
        type=int,
        positional=False,
        description="Specify the page number in the set of paginated records (optional, default = 1).",
    )
    @argument(
        "page_size",
        type=int,
        positional=False,
        description="Specify the number of records to return in each page (optional, default = 10).",
    )
    @command
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the output format of the stdout file (optional, default = json).",
        choices=["json", "table"],
    )
    def runtime_options(self, page: int = 1, page_size: int = 10, output="json") -> int:
        """
        List registered cluster runtimes settings.
        """
        resource = get_factory().load_resource()
        r = resource.list_runtime_options(page=page, page_size=page_size)

        if isinstance(r, int):
            return r

        self._stdout(r["results"], output)
        return 0

    @command(aliases=["op"])
    @argument(
        "page",
        type=int,
        positional=False,
        description="Specify the page number in the set of paginated records (optional, default = 1).",
    )
    @argument(
        "page_size",
        type=int,
        positional=False,
        description="Specify the number of records to return in each page (optional, default = 10).",
    )
    @command
    @argument(
        "output",
        type=str,
        positional=False,
        description="Specify the output format of the stdout file (optional, default = json).",
        choices=["json", "table"],
    )
    def operator_pipelines(
        self, page: int = 1, page_size: int = 10, output="json"
    ) -> int:
        """
        List registered operator pipelines.
        """
        resource = get_factory().load_resource()
        r = resource.list_operator_pipelines(page=page, page_size=page_size)

        if isinstance(r, int):
            return r

        self._stdout(r["results"], output)
        return 0

    @staticmethod
    def _stdout(results, output: str) -> int:
        # Standard Library

        from tabulate import tabulate

        """
            stdout:: TODO: support different format ex: json, tsv, table
        """
        if output == "json":
            cprint(json.dumps(results, indent=4))
        elif output == "table":
            table_header = list(results[0].keys())
            table_datas = [result.values() for result in results]
            cprint(
                tabulate(
                    tabular_data=table_datas, headers=table_header, tablefmt="pipe"
                )
            )
        return 0

    @command
    @argument(
        "run_id",
        type=str,
        positional=False,
        description="Specify the run_id that is going to be delete (required).",
    )
    def delete(self, run_id: str) -> int:
        """
        Delete WES run as well as all the generated output files based on run ID.
        """
        try:
            get_factory().load_resource().delete_run(run_id)
        except requests.HTTPError as e:
            cprint(f"Fail to delete Job {run_id} - '{str(e)}'.", "red")
            return -1

        return 0


@command
class Jobs(BaseJobs):
    """Workflow execution commands"""

    @command
    @argument(
        "working_dir",
        type=str,
        positional=False,
        description="Specify the working directory path that contains request.json (required).",
    )
    def dryrun(self, working_dir: str) -> int:
        """
        Workflow dry run to see if the given request.json files are properly configured by calling seqslab-api/wes/runs/dryrun and seqslab-api/wes/runs/files API.
        """
        if not os.path.isdir(working_dir):
            logging.error("working dir is not a directory")
            cprint("working dir is not a directory", "red")
            return errno.EINVAL

        reqs = [
            os.path.join(working_dir, f)
            for f in os.listdir(working_dir)
            if os.path.isfile(os.path.join(working_dir, f))
            and f.endswith("request.json")
        ]

        for value in enumerate(reqs):
            try:
                with open(value[1], "r") as f:
                    request = json.load(f)
            except json.decoder.JSONDecodeError as e:
                cprint(f"given request not in json format - {e}", "red")

            # wes/${run_id}/dryrun
            mp = MultipartEncoder(
                fields={
                    "name": request.get("name"),
                    "workflow_type": request.get("workflow_type"),
                    "workflow_type_version": request.get("workflow_type_version"),
                    "workflow_url": request.get("workflow_url"),
                    "workflow_params": json.dumps(request.get("workflow_params")),
                    "workflow_backend_params": json.dumps(
                        request.get("workflow_backend_params")
                    ),
                }
            )
            resource = get_factory().load_resource()
            dry_ret = resource.dry_run(
                data=mp,
                headers={"Content-Type": mp.content_type},
                run_request_id=None,
                run_name=request.get("name"),
            )
            dry_res = json.loads(dry_ret.content.decode("utf-8"))

            # wes/${run_id}/files
            res = resource.wes_files(dry_res["run_id"])

            with open(
                os.path.join(working_dir, f'{dry_res["run_id"]}_files.json'), "w"
            ) as f:
                json.dump(res, f, indent=4)

            cprint(
                f"{request.get('name')} verified with dryrun id {dry_res['run_id']}",
                "yellow",
            )

        return 0
