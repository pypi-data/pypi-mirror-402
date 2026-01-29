class WorkflowParamsTemplate:
    def create(self, ex_template: dict, opp_w_args: dict) -> dict:
        operator_pipelines = (
            self.operator_pipelines(ex_template, opp_w_args)
            if "tasks" not in ex_template
            else (ex_template["tasks"])
        )
        return {
            "inputs": ex_template.get("inputs"),
            "datasets": ex_template.get("connections", None),
            "tasks": operator_pipelines,
        }

    def _flat_list(self, v: list, r: list = [], layer: int = 1) -> dict:
        sub_v = []
        for element in v:
            if isinstance(element, list):
                sub_v.extend(element)
            else:
                r.append(element)
        if sub_v:
            layer += 1
            return self._flat_list(sub_v, r, layer)
        return {"list": r, "layer": layer}

    def operator_pipelines(self, ex_template: dict, opp_w_args: dict) -> dict:
        """
        :param: parameter: parameter API response
        :return:
            {
                "e2e.alignmentRun.Bwa.in_file_fastq_r1": {
                    "operators": [""],
                    "description": "demo operator"
                }
            }
        """
        tasks = {}
        pl_keys = [pipeline["id"] for pipeline in ex_template["operator_pipelines"]]
        for k, v in dict(ex_template["i_configs"], **ex_template["o_configs"]).items():
            if not v:
                continue
            assert (
                v in pl_keys
            ), f"given operator pipeline ID {v} for FQN {k} not in operator pipeline list from execs: {pl_keys}"
            for pipeline in ex_template["operator_pipelines"]:
                if pipeline["id"] == v:
                    tasks[k] = {
                        "id": self.norm_pl_key(v, opp_w_args),
                        "operators": pipeline["operators"],
                        "description": pipeline["description"],
                    }
                    continue
        return tasks

    @staticmethod
    def norm_pl_key(pl_key: str, opp_w_args: dict) -> str:
        for opp in opp_w_args:
            if pl_key.startswith(opp):
                return opp
        return pl_key

    @staticmethod
    def inputs_connections(inputs_connection: list = None) -> dict:
        """
        :param:
            parameter = parameter API response
            inputs_json = {
                "e2e.ref_sa": "local_path1",
                "e2e.primer_bedpe": "local_path2",
            }
        :return:
            {
                "arrfqn": [
                    "run_5566/GermlineSnpsIndelsGatk4Hg19.inFileFqs/1",
                    "run_5566/GermlineSnpsIndelsGatk4Hg19.inFileFqs/2"
                    ]
            },
            {
                "auto.match.fqn": null
            }
        """
        for item in inputs_connection:
            v = item.get("cloud", None)
            if v:
                if not isinstance(v, list):
                    item["cloud"] = [v]
                else:
                    ret1 = []
                    for e1 in v:
                        if not isinstance(e1, list):
                            ret1.append(e1)
                        else:
                            ret2 = []
                            for e2 in e1:
                                if not isinstance(e2, list):
                                    ret2.append(e2)
                                else:
                                    raise Exception(
                                        f"More than 3 layer of list is provided {v}"
                                    )
                            ret1.append(ret2)
                    item["cloud"] = ret1
        return inputs_connection


def WorkflowBackendParamsTemplate(
    graph: str,
    clusters: list,
    workspace: str,
    integrity: bool,
    trust: bool,
    token_lifetime: int,
) -> dict:
    ret = {
        "clusters": clusters,
        "workspace": workspace,
        "integrity": integrity,
        "content_trust": trust,
        "token_lifetime": token_lifetime,
        "debug_mode": False,
    }
    if graph:
        ret.update({"graph": graph})
    return ret


def WorkflowBackendParamsClusterTemplate(
    run_time: dict, kernel_version: str, workflow_name: str = ""
) -> dict:
    if kernel_version:
        opts = run_time["options"]
        opts.append(f"seqslab.kernel.version {kernel_version}")
        run_time.update({"options": opts})
    run_time.update({"call": workflow_name})
    return run_time
