# cli code
# Standard Library
import shutil
import uuid
from os.path import abspath, dirname
from typing import List
from unittest import TestCase
from unittest.mock import patch

import arrow
from seqslab.runsheet.runsheet import Run, RunSheet
from seqslab.tests.util import TestShell
from seqslab.trs.register.azure import AzureTRSregister

# cli code
from seqslab.wes.commands import BaseJobs
from seqslab.wes.resource.azure import AzureResource
from seqslab.workspace.commands import BaseWorkspace


def random_string(char_num: int = 25):
    if char_num <= 16:
        return uuid.uuid4().hex[:char_num]
    total_acc = char_num - 16
    random_str = ""
    while total_acc > 0:
        random_str += uuid.uuid4().hex[:total_acc]
        total_acc -= 32
    return random_str + str(int(arrow.utcnow().timestamp() * 1000000))


run_request_id = uuid.uuid4().hex
run_id = uuid.uuid4().hex
wes_data_location = f"{dirname(abspath(__file__))}"
working_dir = f"{wes_data_location}/working-dir/"
fixture_run_name = "HCG398_BGZF"
fixture_run_sheet_csv = f"{working_dir}request-runsheet/run_info_398-fixture.csv"
fixture_run_sheet_csv_v2 = f"{working_dir}request-runsheet/run_info_398-fixtureV2.csv"
fixture_run_sheet_add_reads_csv = (
    f"{working_dir}request-runsheet/run_info_398-fixture-add-reads.csv"
)
fixture_run_sheet_schedule_id_csv = (
    f"{working_dir}request-runsheet/run_info_398-fixture-schedule-id.csv"
)
fixture_execs_fixture_json = "2022-03-30_HCG398_BGZF-execs-fixture.json"
ans_request_json = f"{working_dir}request/2022-03-30_HCG398_BGZF-request-fixture.json"
ans_request_runsheet_json = (
    f"{working_dir}request-runsheet/2022-03-30_HCG398_BGZF-request-fixture.json"
)
ans_request_runsheet_v2_json = (
    f"{working_dir}request-runsheet/2022-03-30_HCG398_BGZF-request-fixture-v2.json"
)

host_name = "dev-api.seqslab.net"
tool_id = "trs_test_4QLix7cSvY"
run_name = random_string()
workflow_url = f"https://{host_name}/trs/v2/tools/{tool_id}/versions/1.0/WDL/files/"


class MockResource(AzureResource):
    def get_run_id(self, run_id) -> dict:
        run_state = "UNKNOWN"
        content = {
            "id": run_id,
            "name": run_name,
            "outputs": [],
            "logs": [],
            "state": run_state,
            "request": {
                "id": 11350,
                "name": run_name,
                "description": None,
                "workflow_type": "WDL",
                "workflow_type_version": "1.0",
                "workflow_params": {
                    "inputs": [
                        {
                            "fqn": "NIPT.refBwt",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta.bwt"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.bwt"
                            ],
                        },
                        {
                            "fqn": "NIPT.refAmb",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta.amb"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.amb"
                            ],
                        },
                        {
                            "fqn": "NIPT.refFa",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta"
                            ],
                        },
                        {
                            "fqn": "NIPT.inputReference",
                            "cloud": [
                                "mnt/storage/reference/RAPIDR_reference/NSBRef200N_GC.RData",
                                "mnt/storage/reference/RAPIDR_reference/NSBRef200N.RData",
                            ],
                            "local": [
                                "/mnt/storage/reference/RAPIDR_reference/NSBRef200N_GC.RData",
                                "/mnt/storage/reference/RAPIDR_reference/NSBRef200N.RData",
                            ],
                        },
                        {
                            "fqn": "NIPT.inFileSpecificRegion",
                            "cloud": [
                                "mnt/storage/reference/ref_doc/Specific_region_new.csv"
                            ],
                            "local": [
                                "/mnt/storage/reference/ref_doc/Specific_region_new.csv"
                            ],
                        },
                        {
                            "fqn": "NIPT.inFileRegion",
                            "cloud": ["mnt/storage/reference/ref_doc/20K.region.csv"],
                            "local": ["/mnt/storage/reference/ref_doc/20K.region.csv"],
                        },
                        {
                            "fqn": "NIPT.inFileGcContent",
                            "cloud": ["mnt/storage/reference/ref_doc/gcContent.csv"],
                            "local": ["/mnt/storage/reference/ref_doc/gcContent.csv"],
                        },
                        {
                            "fqn": "NIPT.refPac",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta.pac"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.pac"
                            ],
                        },
                        {
                            "fqn": "NIPT.inFileCallSexPostiveZxZy",
                            "cloud": [
                                "mnt/storage/reference/ref_doc/callSex_postive_zXzY.csv"
                            ],
                            "local": [
                                "/mnt/storage/reference/ref_doc/callSex_postive_zXzY.csv"
                            ],
                        },
                        {
                            "fqn": "NIPT.inputBaseline",
                            "cloud": [
                                "mnt/storage/reference/RAPIDR_reference/NSBRef200N_GC_binned.ratio.per.region.csv",
                                "mnt/storage/reference/RAPIDR_reference/NSBRef200N_binned.ratio.per.region.csv",
                            ],
                            "local": [
                                "/mnt/storage/reference/RAPIDR_reference/NSBRef200N_GC_binned.ratio.per.region.csv",
                                "/mnt/storage/reference/RAPIDR_reference/NSBRef200N_binned.ratio.per.region.csv",
                            ],
                        },
                        {
                            "fqn": "NIPT.refAnn",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta.ann"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.ann"
                            ],
                        },
                        {
                            "fqn": "NIPT.refSa",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta.sa"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.sa"
                            ],
                        },
                        {
                            "fqn": "NIPT.inFileDataDivide",
                            "cloud": [
                                "mnt/storage/reference/ref_doc/NIPT_data_divid_by_chr_addcounts_autoscan.csv"
                            ],
                            "local": [
                                "/mnt/storage/reference/ref_doc/NIPT_data_divid_by_chr_addcounts_autoscan.csv"
                            ],
                        },
                        {
                            "fqn": "NIPT.inFileBrks",
                            "cloud": ["mnt/storage/reference/ref_doc/brks.csv"],
                            "local": ["/mnt/storage/reference/ref_doc/brks.csv"],
                        },
                        {
                            "fqn": "NIPT.inFileZxZyCase",
                            "cloud": ["mnt/storage/reference/ref_doc/zXzY_case.csv"],
                            "local": ["/mnt/storage/reference/ref_doc/zXzY_case.csv"],
                        },
                        {
                            "fqn": "NIPT.refDict",
                            "cloud": ["mnt/storage/reference/bwa-index_hg19/hg19.dict"],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.dict"
                            ],
                        },
                        {
                            "fqn": "NIPT.inputRead",
                            "cloud": [],
                            "local": [
                                "/mnt/storage/NextSeq550/2021_11_23/FASTQ/21110518_S15_R1_001.fastq.gz"
                            ],
                        },
                        {
                            "fqn": "NIPT.rGcContentRdata",
                            "cloud": [
                                "mnt/storage/reference/RAPIDR_reference/gcContent.RData"
                            ],
                            "local": [
                                "/mnt/storage/reference/RAPIDR_reference/gcContent.RData"
                            ],
                        },
                        {
                            "fqn": "NIPT.refFaFai",
                            "cloud": [
                                "mnt/storage/reference/bwa-index_hg19/hg19.fasta.fai"
                            ],
                            "local": [
                                "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.fai"
                            ],
                        },
                        {
                            "fqn": "NIPT.AutoScan.inFileDataDivide",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.AutoScan.inFileSpecificRegion",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.AutoScan.inFileZscorePerRegion",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bin.inFileBam",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.inFileFastq",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refAmb",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refAnn",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refBwt",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refFa",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refFaFai",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refPac",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Bwa.refSa",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.CNVScan.inFileBaseline",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.CNVScan.inFileBinnedCountsExclBins",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.CNVScan.inFileRegion",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.CNVScan.inFileSpecificRegion",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.DP1WithMNV.inFileVcfGz",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.DP30WithMNV.inFileVcfGz",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FFOnlySnpGC.inFileBrks",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FFOnlySnpGC.inFileGcContent",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FFOnlySnpGC.inFileVCF",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FFOnlySnpGC2DB.inFileVCF",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FFSnp.inFileVCF",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FilterMutectCalls.inFileVcfGz",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FilterMutectCalls.inFileVcfStats",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FilterMutectCalls.inFileVcfTbi",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FilterMutectCalls.refDict",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.FilterMutectCalls.refFaFai",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Mutect2.inFileBam",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Mutect2.refDict",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Mutect2.refFa",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.Mutect2.refFaFai",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.RAPIDR.inFileBin",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.RAPIDR.inFileGcContentRdata",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.RAPIDR.inFileRefRdata",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.ReadCount.inFileBam",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.ReadCount.inFileStats",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.SamtoolsFilter.inFileBam",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.SamtoolsStats.inFileBam",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.ZxZyPlot.inFileCallSexPostiveZxZy",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.ZxZyPlot.inFileTestResults",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                        {
                            "fqn": "NIPT.ZxZyPlot.inFileZxZyCase",
                            "operators": {
                                "format": {
                                    "class": "com.atgenomix.seqslab.piper.operators.format.SingularFormat"
                                },
                                "p_pipe": {
                                    "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                                },
                            },
                            "pipelines": {"call": ["format", "p_pipe"]},
                        },
                    ],
                    "NIPT.refFa": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta",
                    "NIPT.refPac": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.pac",
                    "NIPT.sampleType": "NIPT",
                    "NIPT.inputRead": "/mnt/storage/NextSeq550/2021_11_23/FASTQ/21110518_S15_R1_001.fastq.gz",
                    "NIPT.refSa": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.sa",
                    "NIPT.refAnn": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.ann",
                    "NIPT.barcode": "~{NIPT.inputRead:sample.Order_Overall}",
                    "NIPT.refBwt": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.bwt",
                    "NIPT.inFileZxZyCase": "/mnt/storage/reference/ref_doc/zXzY_case.csv",
                    "NIPT.rGcContentRdata": "/mnt/storage/reference/RAPIDR_reference/gcContent.RData",
                    "NIPT.folderBin": "bin/",
                    "NIPT.inputBaseline": [
                        "/mnt/storage/reference/RAPIDR_reference/NSBRef200N_GC_binned.ratio.per.region.csv",
                        "/mnt/storage/reference/RAPIDR_reference/NSBRef200N_binned.ratio.per.region.csv",
                    ],
                    "NIPT.inFileGcContent": "/mnt/storage/reference/ref_doc/gcContent.csv",
                    "NIPT.refFaFai": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.fai",
                    "NIPT.folderNIPT": "NIPT2.0/",
                    "NIPT.outPathAutoScan": "NIPT2.0/NSBRef200N_GC/AutoScan/",
                    "NIPT.inFileDataDivide": "/mnt/storage/reference/ref_doc/NIPT_data_divid_by_chr_addcounts_autoscan.csv",
                    "NIPT.inFileSpecificRegion": "/mnt/storage/reference/ref_doc/Specific_region_new.csv",
                    "NIPT.folderRAPIDR": "RAPIDR/",
                    "NIPT.heapSizeInGb": "5",
                    "NIPT.plate": "NextSeq550",
                    "NIPT.inFileBrks": "/mnt/storage/reference/ref_doc/brks.csv",
                    "NIPT.refDict": "/mnt/storage/reference/bwa-index_hg19/hg19.dict",
                    "NIPT.inFileRegion": "/mnt/storage/reference/ref_doc/20K.region.csv",
                    "NIPT.refAmb": "/mnt/storage/reference/bwa-index_hg19/hg19.fasta.amb",
                    "NIPT.runDate": "~{NIPT.inputRead:header.Date}",
                    "NIPT.inFileCallSexPostiveZxZy": "/mnt/storage/reference/ref_doc/callSex_postive_zXzY.csv",
                    "NIPT.inputReference": [
                        "/mnt/storage/reference/RAPIDR_reference/NSBRef200N_GC.RData",
                        "/mnt/storage/reference/RAPIDR_reference/NSBRef200N.RData",
                    ],
                    "NIPT.sampleName": "~{NIPT.inputRead:sample.Sample_ID}",
                },
                "workflow_backend_params": {
                    "workspace": "seqslabwu2",
                    "clusters": [
                        {
                            "id": 2,
                            "call": "NIPT",
                            "name": "acu-m8",
                            "description": "Memory optimized 8-core cluster compute (Runtime 2.0, Spark 3.3, Python 3.8, Java 1.8.0, Cromwell 63)",
                            "settings": {
                                "type": "batch.core.windows.net",
                                "vm_size": "Standard_D13_v2",
                                "workers": {"spot": 0, "dedicated": 1},
                                "auto_scale": False,
                                "worker_on_master": True,
                            },
                            "options": [
                                "spark.driver.cores 1",
                                "spark.driver.memory 536870912",
                                "spark.executor.cores 1",
                                "spark.executor.memory 7g",
                                "spark.dynamicAllocation.enabled true",
                                "spark.shuffle.service.enabled true",
                                "spark.dynamicAllocation.minExecutors 1",
                                "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                                "spark.local.dir /mnt",
                            ],
                        }
                    ],
                    "integrity": True,
                    "content_trust": False,
                    "debug_mode": True,
                },
                "workflow_url": workflow_url,
                "tags": [],
            },
            "start_time": None,
            "end_time": None,
        }

        return content

    def get_run_status(self, run_id) -> dict:
        run_state = "UNKNOWN"
        return {"run_id": run_id, "state": run_state}

    def sync_run_jobs(self, data, headers, run_request_id, run_name, rerun_id=None):
        class ReturnR:
            def __init__(self, data):
                self.data = data

            @property
            def content(self):
                return str({}).encode("utf-8")

        response = ReturnR(data=headers)
        return response

    def get_runtime_setting(self, runtime_name: str) -> dict:
        return {
            "id": 1,
            "name": "acu-m4",
            "description": "Memory optimized 4-core cluster compute with a maximum of 500 concurrent tasks (Runtime 2.0, Spark 3.3, Python 3.8, Java 1.8.0, Cromwell 78)",
            "settings": {
                "type": "batch.core.windows.net",
                "vm_size": "Standard_D12_v2",
                "wm_size": "Standard_D1_v2",
                "workers": {"spot": 0, "dedicated": 1},
                "auto_scale": False,
                "worker_on_master": True,
            },
            "options": [
                "spark.driver.cores 1",
                "spark.driver.memory 536870912",
                "spark.executor.cores 1",
                "spark.executor.memory 7g",
                "spark.dynamicAllocation.enabled true",
                "spark.shuffle.service.enabled true",
                "spark.dynamicAllocation.minExecutors 1",
                "spark.serializer org.apache.spark.serializer.KryoSerializer",
                "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                "spark.executor.extraJavaOptions -XX:+UseG1GC",
                "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                "spark.local.dir /mnt",
                "spark.port.maxRetries 64",
            ],
        }

    def list_operator_pipelines(self, page, page_size) -> dict:
        return {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": "Delta",
                    "description": "Designed for DataFrame workloads associated with tasks utilizing SQL commands.",
                    "file_type": "delta",
                    "workload_type": "DataframeTable",
                    "input": True,
                    "operators": ["TableLocalizationExecutor"],
                    "upstreams": [],
                    "version": "2022-12-01",
                },
                {
                    "id": "DeltaToCsvWriter",
                    "description": "Designed for delocalizing DataFrames outputted from tasks utilizing SQL commands and saving to a CSV file.",
                    "file_type": "csv,tsv,csv.gz,tsv.gz",
                    "workload_type": "DataframeFile",
                    "input": False,
                    "operators": [
                        "SqlDefaultCollector",
                        {
                            "name": "CsvWriter",
                            "arguments": {
                                "header": "true",
                                "delimiter": ",",
                                "partitionNum": "1",
                            },
                        },
                    ],
                    "upstreams": ["Delta", "CsvToDelta", "CsvToDeltaIndex"],
                    "version": "2023-11-17",
                },
            ],
        }

    def schedule_run(self, data: dict):
        class ReturnR:
            def __init__(self, data):
                self.data = data

            def json(self):
                return {
                    "id": 123,
                    "schedule": {
                        "id": 456,
                        "schedule_type": "O",
                        "next_run": "2024-05-28T00:11:00Z",
                        "cron": None,
                    },
                }

            @property
            def content(self):
                return str({}).encode("utf-8")

        response = ReturnR(data=data)
        return response

    def get_schedule(self, schedule_id: str):
        return {
            "id": 197,
            "schedule": {
                "id": 4855,
                "schedule_type": "O",
                "next_run": "2024-08-22T10:00:00Z",
                "cron": None,
            },
            "request": {
                "id": 1446,
                "name": "HCG398_BGZF",
                "workflow_params": {
                    "inputs": {
                        "GermlineSnpsIndelsGatk4.inFileFqs": [
                            "HCG398_BGZF_r1.fastq.gz",
                            "HCG398_BGZF_r2.fastq.gz",
                        ],
                        "GermlineSnpsIndelsGatk4.sampleName": "~{GermlineSnpsIndelsGatk4.inFileFqs/1:sample.Sample_ID}",
                        "GermlineSnpsIndelsGatk4.refName": "hg19",
                        "GermlineSnpsIndelsGatk4.refFa": "hg19/ref.fa",
                        "GermlineSnpsIndelsGatk4.refFai": "hg19/ref.fa.fai",
                        "GermlineSnpsIndelsGatk4.refDict": "hg19/ref.dict",
                        "GermlineSnpsIndelsGatk4.refSa": "hg19/ref.fa.sa",
                        "GermlineSnpsIndelsGatk4.refAnn": "hg19/ref.fa.ann",
                        "GermlineSnpsIndelsGatk4.refBwt": "hg19/ref.fa.bwt",
                        "GermlineSnpsIndelsGatk4.refPac": "hg19/ref.fa.pac",
                        "GermlineSnpsIndelsGatk4.refAmb": "hg19/ref.fa.amb",
                        "GermlineSnpsIndelsGatk4.dbsnpVCF": "hg19/DbSNP.vcf.gz",
                        "GermlineSnpsIndelsGatk4.dbsnpVCFTbi": "hg19/DbSNP.vcf.gz.tbi",
                        "GermlineSnpsIndelsGatk4.knownIndelsSitesVCFs": [
                            "hg19/Homo_sapiens_known_indels.vcf.gz",
                            "hg19/Mills_and_1000G_gold_standard.indels.vcf.gz",
                        ],
                        "GermlineSnpsIndelsGatk4.knownIndelsSitesIdxs": [
                            "hg19/Homo_sapiens_known_indels.vcf.gz.tbi",
                            "hg19/Mills_and_1000G_gold_standard.indels.vcf.gz.tbi",
                        ],
                        "GermlineSnpsIndelsGatk4.makeGVCF": True,
                        "GermlineSnpsIndelsGatk4.makeBamout": False,
                        "GermlineSnpsIndelsGatk4.gatk_path": "/gatk/gatk-4.2.0.0/gatk",
                        "GermlineSnpsIndelsGatk4.gotc_path": "/usr/bin/",
                        "GermlineSnpsIndelsGatk4.bwaCommandline": "bwa mem -K 100000000 -v 3 -t 2 -Y $bash_ref_fasta",
                        "GermlineSnpsIndelsGatk4.executorMemory": 9,
                    },
                    "datasets": {
                        "GermlineSnpsIndelsGatk4.inFileFqs": None,
                        "GermlineSnpsIndelsGatk4.refFa": "hg19/ref.fa",
                        "GermlineSnpsIndelsGatk4.refFai": "hg19/ref.fa.fai",
                        "GermlineSnpsIndelsGatk4.refDict": "hg19/ref.dict",
                        "GermlineSnpsIndelsGatk4.refSa": "hg19/ref.fa.sa",
                        "GermlineSnpsIndelsGatk4.refAnn": "hg19/ref.fa.ann",
                        "GermlineSnpsIndelsGatk4.refBwt": "hg19/ref.fa.bwt",
                        "GermlineSnpsIndelsGatk4.refPac": "hg19/ref.fa.pac",
                        "GermlineSnpsIndelsGatk4.refAmb": "hg19/ref.fa.amb",
                        "GermlineSnpsIndelsGatk4.dbsnpVCF": "hg19/DbSNP.vcf.gz",
                        "GermlineSnpsIndelsGatk4.dbsnpVCFTbi": "hg19/DbSNP.vcf.gz.tbi",
                        "GermlineSnpsIndelsGatk4.knownIndelsSitesVCFs": [
                            "hg19/Homo_sapiens_known_indels.vcf.gz",
                            "hg19/Mills_and_1000G_gold_standard.indels.vcf.gz",
                        ],
                        "GermlineSnpsIndelsGatk4.knownIndelsSitesIdxs": [
                            "hg19/Homo_sapiens_known_indels.vcf.gz.tbi",
                            "hg19/Mills_and_1000G_gold_standard.indels.vcf.gz.tbi",
                        ],
                    },
                    "tasks": {
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.inFileFastqR1": {
                            "id": "opp_input_fastq_partition_per-1M-reads",
                            "operators": ["FastqPartitioner", "FastqExecutor"],
                            "description": "File-based (FASTQ) workload parallelization pipeline with 1,048,576 read records for each partition",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.inFileFastqR2": {
                            "id": "opp_input_fastq_partition_per-1M-reads",
                            "operators": ["FastqPartitioner", "FastqExecutor"],
                            "description": "File-based (FASTQ) workload parallelization pipeline with 1,048,576 read records for each partition",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_alt": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_amb": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_ann": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_bwt": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_dict": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_fasta": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_fasta_index": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_pac": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_sa": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.MarkDuplicates.input_bam": {
                            "id": "opp_input_bam_partition_hg19-part155",
                            "operators": ["BamPartitionerHg19Part155", "BamExecutor"],
                            "description": "File-based (BAM) workload pipeline with reads on the hg19 reference genome parallelized into 155 contiguous unmasked regions",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.ref_dict": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.ref_fasta": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.ref_fasta_index": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.dbSNP_vcf": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.dbSNP_vcf_index": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.known_indels_sites_VCFs": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.known_indels_sites_indices": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.ref_dict": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.ref_fasta": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.ref_fasta_index": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.ref_dict": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.ref_fasta": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.ref_fasta_index": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.IndexBam.inFileBam": {
                            "id": "opp_input_bam_partition_1",
                            "operators": ["BamPartitionerPart1", "BamExecutor"],
                            "description": "File-based (BAM) workload pipeline with all records in a single partition",
                        },
                        "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.ref_dict": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.ref_fasta": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.ref_fasta_index": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.GenotypeGVCFs.dbsnpVCF": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.GenotypeGVCFs.dbsnpVCFTbi": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.GenotypeGVCFs.inFileGVCF": {
                            "id": "opp_input_vcf_partition_hg19-3109",
                            "operators": [
                                "VcfPartitionerHg19Part3109",
                                "VcfDataFrameTransformer",
                                "VcfExecutor",
                            ],
                            "description": "File-based (VCF) workload pipeline with the hg19 reference genome parallelized into 3,109 contiguous unmasked regions",
                        },
                        "GermlineSnpsIndelsGatk4.GenotypeGVCFs.refDict": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.GenotypeGVCFs.refFa": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                        "GermlineSnpsIndelsGatk4.GenotypeGVCFs.refFai": {
                            "id": "opp_input_default",
                            "operators": ["RefLoader"],
                            "description": "Automatic workload pipeline for localizing either a file or a directory in a single node cluster",
                        },
                    },
                },
                "workflow_backend_params": {
                    "clusters": [
                        {
                            "id": 1,
                            "name": "acu-m4",
                            "description": "Memory optimized 4-core cluster compute with a maximum of 500 concurrent tasks (Runtime 2.0, Spark 3.3, Python 3.8, Java 1.8.0, Cromwell 78)",
                            "settings": {
                                "type": "batch.core.windows.net",
                                "vm_size": "Standard_D12_v2",
                                "wm_size": "Standard_D1_v2",
                                "workers": {"spot": 0, "dedicated": 1},
                                "auto_scale": False,
                                "worker_on_master": True,
                            },
                            "options": [
                                "spark.driver.cores 1",
                                "spark.driver.memory 536870912",
                                "spark.executor.cores 1",
                                "spark.executor.memory 7g",
                                "spark.dynamicAllocation.enabled true",
                                "spark.shuffle.service.enabled true",
                                "spark.dynamicAllocation.minExecutors 1",
                                "spark.serializer org.apache.spark.serializer.KryoSerializer",
                                "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                                "spark.executor.extraJavaOptions -XX:+UseG1GC",
                                "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                                "spark.local.dir /mnt",
                                "spark.port.maxRetries 64",
                            ],
                            "call": "GermlineSnpsIndelsGatk4",
                        }
                    ],
                    "workspace": "test",
                    "integrity": False,
                    "content_trust": False,
                    "token_lifetime": 24,
                    "debug_mode": False,
                    "graph": 'digraph GermlineSnpsIndelsGatk4 {\n  #rankdir=LR;\n  compound=true;\n\n  # Links\n  CALL_PreProcessingForVariantDiscovery_GATK4 -> CALL_GenotypeGVCFs\n  CALL_HaplotypeCallerGvcf_GATK4 -> CALL_GenotypeGVCFs\n  CALL_PreProcessingForVariantDiscovery_GATK4 -> CALL_HaplotypeCallerGvcf_GATK4\n  CALL_PreProcessingForVariantDiscovery_GATK4 -> CALL_IndexBam\n\n  # Nodes\n  CALL_GenotypeGVCFs [label="call GenotypeGVCFs"]\n  CALL_PreProcessingForVariantDiscovery_GATK4 [label="call PreProcessingForVariantDiscovery_GATK4";shape="oval";peripheries=2]\n  CALL_HaplotypeCallerGvcf_GATK4 [label="call HaplotypeCallerGvcf_GATK4";shape="oval";peripheries=2]\n  CALL_IndexBam [label="call IndexBam"]\n}',
                },
                "workflow_url": "https://dev-api.seqslab.net/trs/v2/tools/trs_gatk_germline_hg19_dev/versions/1.0/WDL/files/",
                "workflow_type_version": "1.0",
                "workflow_type": "WDL",
                "tags": "2022-3-30/HCG398_BGZF",
            },
        }


class MockTrsResource(AzureTRSregister):
    # trs mock
    @staticmethod
    def get_execs_json(workflow_url: str, download_path: str):
        shutil.copyfile(
            f"{working_dir}request/{fixture_execs_fixture_json}", download_path
        )


class MockJobs(BaseJobs):
    """
    Mock Job commands
    """


class MockRunSheet(RunSheet):
    def __init__(self, path=None) -> None:
        self._runs = []
        self._parse_run()


class MockRun(Run):
    def __init__(self, path=None) -> None:
        self._runs = []
        self._parse_run()


job_patch = patch("seqslab.wes.commands.Jobs", MockJobs)
resource_patch = patch("seqslab.wes.resource.base.BaseResource", MockResource)
resource_trs_patch = patch(
    "seqslab.trs.register.azure.AzureTRSregister", MockTrsResource
)

run_sheet_patch = patch("seqslab.runsheet.runsheet.RunSheet", MockRunSheet)
run_patch = patch("seqslab.runsheet.runsheet.kRun", MockRun)


class mock_Workspace(BaseWorkspace):
    """Mock workspace commands"""

    def __init__(self):
        pass

    @staticmethod
    def list_workspaces(**kwargs) -> List[dict]:
        return [
            {
                "id": "/subscriptions/ae6bdb0d-b2b4-4de4-9d5d-42797243a36e/resourceGroups/cmubdcwus2",
                "name": "cmubdcwus2",
                "location": "westus2",
            }
        ]

    @staticmethod
    def validate_workspace(query: str, backend: str) -> bool:
        return True


resource_workspace_patch = patch(
    "seqslab.workspace.resource.azure.AzureResource", mock_Workspace
)


class BasicTest(TestCase):
    mock_command = MockJobs()
    workspace = "test"
    shell = TestShell

    @staticmethod
    def get_loop():
        # Standard Library
        import asyncio

        # because there are no current event loop in thread 'MainThread' in pytest, we need to add the loop to initial new loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception:
            pass


@job_patch
@resource_patch
@resource_workspace_patch
class CommandSpecTest(BasicTest):
    def test_get_run_info(self):
        self.get_loop()
        run_id = "run_" + random_string(15)
        shell = self.shell(commands=[self.mock_command.get])
        exit_code = shell.run_cli_line(f"test_shell get --run-id {run_id}")
        assert exit_code == 0

    def test_run(self):
        shell = self.shell(commands=[self.mock_command.run])
        exit_code = shell.run_cli_line(
            f"test_shell run --working-dir {working_dir} --workspace test"
        )
        assert exit_code == 0

    def test_schedule(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.schedule])
        exit_code = shell.run_cli_line(
            f"test_shell schedule --request-path {ans_request_runsheet_json} --date 2024-05-28 --time 10:00 "
            f"--workspace test"
        )
        assert exit_code == 0

    def test_run_state(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.run_state])
        exit_code = shell.run_cli_line(f"test_shell run-state --run-id {run_id}")
        assert exit_code == 0

    def test_rerun(self):
        shell = self.shell(commands=[self.mock_command.rerun])
        cmd = f"test_shell rerun --rerun-id {run_id}"
        print(f"test command: {cmd}")
        exit_code = shell.run_cli_line(cmd)
        assert exit_code == 0


@job_patch
@resource_patch
@resource_trs_patch
@resource_workspace_patch
class CreateJobsTest(BasicTest):
    mock_command = MockJobs()

    @staticmethod
    def req_validate(query_path, ans_path):
        # Standard Library
        import json

        with open(query_path, "r") as f:
            query_json = json.load(f)
        with open(ans_path, "r") as f:
            ans_json = json.load(f)
        TestCase().assertDictEqual(query_json, ans_json)

    def test_request_runsheet(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.request_runsheet])
        exit_code = shell.run_cli_line(
            f"test_shell request-runsheet --seq-run-id Date --run-sheet {fixture_run_sheet_csv} --working-dir "
            f"{working_dir}request-runsheet --workspace test --fq-sig ~{{Sample_ID}} --token-lifetime 24"
        )
        self.req_validate(
            f"{working_dir}request-runsheet/{fixture_run_name}-request.json",
            ans_request_runsheet_json,
        )
        assert exit_code == 0

    def test_add_reads_runsheet(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.request_runsheet])
        exit_code = shell.run_cli_line(
            f"test_shell request-runsheet --seq-run-id Date --run-sheet {fixture_run_sheet_add_reads_csv} --working-dir "
            f"{working_dir}request-runsheet --workspace test --fq-sig ~{{Sample_ID}} --token-lifetime 24"
        )

        self.req_validate(
            f"{working_dir}request-runsheet/{fixture_run_name}-request.json",
            ans_request_runsheet_json,
        )

        assert exit_code == 0

    def test_request_runsheet_v2(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.request_runsheet])
        exit_code = shell.run_cli_line(
            f"test_shell request-runsheet --seq-run-id RunName --run-sheet {fixture_run_sheet_csv_v2} --working-dir "
            f"{working_dir}request-runsheet --workspace test --fq-sig ~{{Sample_ID}} --token-lifetime 24"
        )
        self.req_validate(
            f"{working_dir}request-runsheet/{fixture_run_name}-request.json",
            ans_request_runsheet_v2_json,
        )
        assert exit_code == 0

    def test_add_reads_runsheet_schedule(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.request_runsheet])
        exit_code = shell.run_cli_line(
            f"test_shell request-runsheet --seq-run-id Date --run-sheet {fixture_run_sheet_schedule_id_csv} --working-dir "
            f"{working_dir}request-runsheet --workspace test --fq-sig ~{{Sample_ID}} --token-lifetime 24"
        )
        self.req_validate(
            f"{working_dir}request-runsheet/{fixture_run_name}-request.json",
            ans_request_runsheet_json,
        )
        assert exit_code == 0

    def test_request(self):
        self.get_loop()
        shell = self.shell(commands=[self.mock_command.request])
        exit_code = shell.run_cli_line(
            f"test_shell request --workflow-url {workflow_url} --run-name {fixture_run_name} "
            f"--working-dir {working_dir}request --execs {fixture_execs_fixture_json} --workspace test --token-lifetime 24"
        )
        self.req_validate(
            f"{working_dir}request/{fixture_run_name}-request.json", ans_request_json
        )
        assert exit_code == 0


if __name__ == "__main__":
    test = CommandSpecTest()
    test.setUp()
    test.test_get_run_info()
    test.test_schedule()
    test.test_run()
    test.test_run_state()
    test.test_rerun()

    job_test = CreateJobsTest()
    job_test.test_request()
    job_test.test_request_runsheet()
    job_test.test_add_reads_runsheet()
