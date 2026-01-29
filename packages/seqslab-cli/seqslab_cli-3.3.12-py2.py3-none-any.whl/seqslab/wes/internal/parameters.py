# Standard Library
import errno
import json
import os
import re
import zipfile

from seqslab.runsheet.runsheet import Run
from seqslab.wes.resource.common import get_factory
from seqslab.wes.template.base import (
    WorkflowBackendParamsClusterTemplate,
    WorkflowBackendParamsTemplate,
    WorkflowParamsTemplate,
)
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


def label2fqn(run: Run):
    r1fqn = set(
        list(
            map(
                lambda sample: (
                    re.sub(r"(/\d+)*$", "", sample.Read1_Label),
                    ".".join(re.sub(r"(/\d+)*$", "", sample.Read1_Label).split("/")),
                ),
                run.samples,
            )
        )
    )
    r2fqn = set(
        list(
            map(
                lambda sample: (
                    re.sub(r"(/\d+)*$", "", sample.Read2_Label),
                    ".".join(re.sub(r"(/\d+)*$", "", sample.Read2_Label).split("/")),
                ),
                run.samples,
            )
        )
    )
    if not r1fqn and not r2fqn:
        raise Exception(
            "runsheet template without Read1_Label and Read2_Label assignment"
        )
    # normalize r1fqn and r2fqn length
    list_r2fqn = (
        list(r2fqn) if len(r2fqn) == len(r1fqn) else [("", "") for item in r1fqn]
    )
    return list(r1fqn), list_r2fqn


def is_castable_to_int(s):
    try:
        int(s)  # Try to convert the string to an integer
        return True  # If successful, it's castable to an integer
    except ValueError:
        return False


def populate_fqn(labels: list, names: list):
    dim = []
    sample_indices = []

    for idx in range(len(labels)):
        lb1s = labels[idx].split("/")

        # label without indices => len(Samples) should be one
        if not is_castable_to_int(lb1s[-1]):
            assert len(labels) == 1
            return f"{names[idx]}.fastq.gz"

        # label with 1d indices
        if not is_castable_to_int(lb1s[-2]):
            dim.append(1)
            sample_indices.append([int(lb1s[-1]) - 1])
        else:
            if is_castable_to_int(lb1s[-3]):
                raise ValueError("SeqsLab does not support FQN higher than 2 dimension")
            dim.append(2)
            sample_indices.append([int(lb1s[-2]) - 1, int(lb1s[-1]) - 1])

    assert len(set(dim)) == 1

    if dim[0] == 2:
        d1_size = max([ind[0] for ind in sample_indices]) + 1
        d2_size = max([ind[1] for ind in sample_indices]) + 1
        ret = [["" for _ in range(d2_size)] for _ in range(d1_size)]
        for i in range(len(labels)):
            indices = sample_indices[i]
            ret[indices[0]][indices[1]] = f"{names[i]}.fastq.gz"
        ret = [[item for item in inner_list if item != ""] for inner_list in ret]
    else:
        d1_size = max([ind[0] for ind in sample_indices]) + 1
        ret = ["" for i in range(d1_size)]
        for i in range(len(labels)):
            index = sample_indices[i]
            ret[index[0]] = f"{names[i]}.fastq.gz"

    return ret


def _fastq_expr(rule: str, meta: dict) -> str:
    pattern = r"~{([\w]+)}"
    matches = re.findall(pattern, rule)
    expr = rule
    for m in matches:
        meta_val = meta[m]
        expr = expr.replace(f"~{{{m}}}", str(meta_val))
    return expr


def validate_execs(exec_content: dict):
    inputs = exec_content.get("inputs")
    datasets = exec_content.get("connections")
    for fqn in datasets:
        if fqn not in inputs:
            cprint(f"datasets FQN {fqn} not in inputs.json", "red")
            return False
    return True


def runsheet_rendering(params: dict, run: Run, fq_sig: str, is_single_end: bool):
    # inputs.json rendering based on runsheet info for both normal runs and add-reads runs, also reset datasets section
    tpl_r1fqn, tpl_r2fqn = label2fqn(run)
    for idx in range(0, len(tpl_r1fqn)):
        r1lbpfx = tpl_r1fqn[idx][0]
        r2lbpfx = tpl_r2fqn[idx][0]
        lb1 = []
        lb2 = []
        na1 = []
        na2 = []
        for sa in run.samples:
            info_dic = {k.replace(" ", "_"): v for k, v in sa.to_json().items()}

            lbo1 = sa.Read1_Label
            lba1 = sa.to_json().get("Add_Read1_Label", "")
            if r1lbpfx in lbo1:
                lb1.append(lbo1)
                na1.append(f"{_fastq_expr(fq_sig, info_dic)}_r1")
            if r1lbpfx in lba1:
                lb1.append(lba1)
                na1.append(f"{_fastq_expr(fq_sig, info_dic)}_org_r1")

            lbo2 = sa.Read2_Label
            lba2 = sa.to_json().get("Add_Read2_Label", "")
            if r2lbpfx in lbo2:
                lb2.append(lbo2)
                na2.append(f"{_fastq_expr(fq_sig, info_dic)}_r2")
            if r2lbpfx in lba2:
                lb2.append(lba2)
                na2.append(f"{_fastq_expr(fq_sig, info_dic)}_org_r2")

        r1fqn = tpl_r1fqn[idx][1]
        r2fqn = tpl_r2fqn[idx][1]
        if r1fqn == r2fqn:
            params["inputs"][r1fqn] = populate_fqn(lb1 + lb2, na1 + na2)
            params["datasets"][r1fqn] = None
            return params
        else:
            params["inputs"][r1fqn] = populate_fqn(lb1, na1)
            params["datasets"][r1fqn] = None

        if r2fqn:
            assert is_single_end is False, "R2FQN should not be set for single end run"
            params["inputs"][r2fqn] = populate_fqn(lb2, na2)
            params["datasets"][r2fqn] = None

    return params


def workflow_params(
    execs_json: str,
    opp_w_args: list,
) -> dict:
    """
    Create workflow_params.json.
    """
    # TODO: write DRS id to workflow_params based run_sheet content
    if not os.path.isfile(execs_json):
        cprint(f"{execs_json} does not exist", "red")
        return errno.ENOENT

    try:
        with open(execs_json, "r") as f:
            t_content = json.loads(f.read())
            if not validate_execs(t_content):
                return errno.EINVAL

        params = WorkflowParamsTemplate().create(
            ex_template=t_content, opp_w_args=opp_w_args
        )
        return params
    except zipfile.BadZipfile as error:
        cprint(f"{error}", "red")
        return errno.EPIPE
    except json.JSONDecodeError as error:
        cprint(f"{error}", "red")
        return errno.EPIPE
    except KeyError as error:
        cprint(f"{error}", "red")
        return errno.ESRCH
    except LookupError as error:
        cprint(f"{error}", "red")
        return errno.ESRCH


def workflow_backend_params(
    execs_json: str,
    workspace: str,
    runtimes: str = None,
    integrity: bool = False,
    trust: bool = False,
    kernel_version: str = "",
    token_lifetime: int = 2,
) -> dict:
    """
    Create workflow_backend_params.json.
    """
    if not os.path.isfile(execs_json):
        cprint(f"{execs_json} does not exist", "red")
        return errno.ENOENT
    try:
        with open(execs_json, "r") as f:
            execs = json.loads(f.read())
            workflow = execs.get("workflows")
            primary_obj = [
                item
                for item in workflow
                if item.get("file_type") == "PRIMARY_DESCRIPTOR"
            ][0]
            primary_workflow_name = (
                primary_obj.get("workflow_name")
                if primary_obj.get("workflow_name")
                else primary_obj.get("name").replace(".wdl", "")
            )
            call_names_list = execs.get("calls", None)
            # use sub-workflow names if no call section given
            if not call_names_list:
                calls = [
                    item.get("name").replace(".wdl", "")
                    for item in workflow
                    if item.get("file_type") == "SECONDARY_DESCRIPTOR"
                ] + [primary_workflow_name]
            else:
                calls = call_names_list
    except json.JSONDecodeError as error:
        cprint(f"{error}", "red")
        return errno.EPIPE

    rt_dict = {}
    if not runtimes:
        rt_dict = {primary_workflow_name: "m4-cluster"}
    else:
        rtcs = runtimes.split(":")
        for rtc in rtcs:
            c = rtc.split("=")
            rt_dict[c[0]] = c[1]

    resource = get_factory().load_resource()
    clusters = []
    for k, v in rt_dict.items():
        if k not in calls:
            raise RuntimeError(
                f"given call name {k} not in TRS registered call name list {calls}!"
            )
        clusters.append(
            WorkflowBackendParamsClusterTemplate(
                run_time=resource.get_runtime_setting(v),
                workflow_name=k,
                kernel_version=kernel_version,
            )
        )

    bk_template = WorkflowBackendParamsTemplate(
        graph=execs.get("graph"),
        clusters=clusters,
        workspace=workspace,
        integrity=integrity,
        trust=trust,
        token_lifetime=token_lifetime,
    )
    return bk_template
