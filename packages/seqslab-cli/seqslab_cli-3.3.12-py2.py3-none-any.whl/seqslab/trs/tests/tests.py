# Standard Library
import json
import random
import string
from functools import lru_cache
from os.path import abspath, dirname, join
from typing import List
from unittest import TestCase
from unittest.mock import patch

from seqslab.tests.util import TestShell
from seqslab.trs.commands import BaseTools
from seqslab.trs.register.azure import AzureTRSregister
from seqslab.trs.resource.azure import AzureResource
from seqslab.workspace.commands import BaseWorkspace
from tenacity import retry, stop_after_attempt, wait_fixed


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
@lru_cache(maxsize=16)
def mock_parameter(primary_descriptor: str, zip_file: str):
    return {
        "workflows": [
            {
                "name": "haplotypecaller-gvcf-gatk4.wdl",
                "path": "GATK-Germline-Snps-Indels/wdl/subworkflows/haplotypecaller-gvcf-gatk4.wdl",
                "file_type": "SECONDARY_DESCRIPTOR",
                "workflow_name": "HaplotypeCallerGvcf_GATK4",
                "image_name": "",
            },
            {
                "name": "processing-for-variant-discovery-gatk4.wdl",
                "path": "GATK-Germline-Snps-Indels/wdl/subworkflows/processing-for-variant-discovery-gatk4.wdl",
                "file_type": "SECONDARY_DESCRIPTOR",
                "workflow_name": "PreProcessingForVariantDiscovery_GATK4",
                "image_name": "",
            },
            {
                "name": "GATK-Germline-Snps-Indels-main.wdl",
                "path": "GATK-Germline-Snps-Indels/wdl/GATK-Germline-Snps-Indels-main.wdl",
                "file_type": "PRIMARY_DESCRIPTOR",
                "workflow_name": "GermlineSnpsIndelsGatk4",
                "image_name": "",
            },
            {
                "name": "tasks.wdl",
                "path": "GATK-Germline-Snps-Indels/wdl/subworkflows/tasks.wdl",
                "file_type": "SECONDARY_DESCRIPTOR",
                "workflow_name": "",
                "image_name": "",
            },
            {
                "name": "",
                "path": "GATK-Germline-Snps-Indels/execs/gatk.parallel.hg19.0713.execs.json",
                "file_type": "TEST_FILE",
            },
            {
                "name": "",
                "path": "GATK-Germline-Snps-Indels/inputs/GATK-Germline-Snps-Indels-inputs.json",
                "file_type": "TEST_FILE",
            },
        ],
        "subgraphs": [
            'digraph HaplotypeCallerGvcf_GATK4 {\n  #rankdir=LR;\n  compound=true;\n\n  # Links\n  \n\n  # Nodes\n  CALL_HaplotypeCaller [label="call HaplotypeCaller"]\n}\n',
            'digraph PreProcessingForVariantDiscovery_GATK4 {\n  #rankdir=LR;\n  compound=true;\n\n  # Links\n  CALL_BaseRecalibrator -> CALL_ApplyBQSR\n  CALL_SortAndFixTags -> CALL_BaseRecalibrator\n  CALL_SortAndFixTags -> CALL_ApplyBQSR\n  CALL_BwaMem -> CALL_MarkDuplicates\n  CALL_Fastp -> CALL_BwaMem\n  CALL_MarkDuplicates -> CALL_SortAndFixTags\n\n  # Nodes\n  CALL_Fastp [label="call Fastp"]\n  CALL_ApplyBQSR [label="call ApplyBQSR"]\n  CALL_SortAndFixTags [label="call SortAndFixTags"]\n  CALL_BwaMem [label="call BwaMem"]\n  CALL_MarkDuplicates [label="call MarkDuplicates"]\n  CALL_BaseRecalibrator [label="call BaseRecalibrator"]\n}\n',
        ],
        "runtime_options": [
            {
                "id": 1,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D12_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 0, "dedicated": 1},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-cluster",
                "description": "4 vCPUs and 28 GiB of memory (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 536870912",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 2,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D13_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 0, "dedicated": 1},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-xcluster",
                "description": "8 vCPUs and 56 GiB of memory (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 3,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D13_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 2, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-2xcluster",
                "description": "16 vCPUs and 112 GiB of memory featuring distributed spot instances (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 4,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D13_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 8, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-8xcluster",
                "description": "64 vCPUs and 448 GiB of memory featuring distributed spot instances (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 5,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D13_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 10, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-10xcluster",
                "description": "80 vCPUs and 560 GiB of memory featuring distributed spot instances and well-suited for tasks requiring significant parallel processing power (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 6,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D14_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 10, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-20xcluster",
                "description": "160 vCPUs and 1120 GiB of memory featuring distributed spot instances and well-suited for tasks requiring significant parallel processing power (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 7,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_D14_v2",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 30, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "m4-60xcluster",
                "description": "480 vCPUs and 3360 GiB of memory featuring distributed spot instances and well-suited for tasks requiring significant parallel processing power (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 7g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 8,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_NC16as_T4_v3",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 1, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "g4-2xcluster",
                "description": "16 vCPUs, 110 GiB of memory, and 1 Tesla T4 GPU (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 64g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 9,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_NC64as_T4_v3",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 1, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "g4-8xcluster",
                "description": "64 vCPUs, 440 GiB of memory, and 4 Tesla T4 GPUs (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 300g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
            {
                "id": 10,
                "settings": {
                    "type": "batch.core.windows.net",
                    "vm_size": "Standard_NC8as_T4_v3",
                    "wm_size": "Standard_D1_v2",
                    "workers": {"spot": 40, "dedicated": 0},
                    "auto_scale": False,
                    "worker_on_master": True,
                },
                "name": "g4-40xcluster",
                "description": "320 vCPUs, 2240 GiB of memory, and 40 Tesla T4 GPUs featuring distributed spot instances (Runtime 1.5, Cromwell 78, Spark 3.3, Python 3.8, Java 1.8.0)",
                "options": [
                    "spark.driver.cores 1",
                    "spark.driver.memory 2g",
                    "spark.executor.cores 1",
                    "spark.executor.memory 25g",
                    "spark.dynamicAllocation.enabled True",
                    "spark.shuffle.service.enabled True",
                    "spark.dynamicAllocation.minExecutors 1",
                    "spark.serializer org.apache.spark.serializer.KryoSerializer",
                    "spark.kryo.registrator org.bdgenomics.adam.serialization.ADAMKryoRegistrator",
                    "spark.executor.extraJavaOptions -XX:+UseG1GC",
                    "spark.hadoop.io.compression.codecs org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    "spark.local.dir /mnt",
                    "spark.port.maxRetries 64",
                ],
            },
        ],
        "operator_pipelines": [
            {
                "id": "opp_bam_auto-path",
                "description": "File-based (BAM/SAM) workload pipeline without data parallelization",
                "file_type": "bam,sam",
                "workload_type": "FILE",
                "input": True,
                "operators": {
                    "format": {
                        "class": "com.atgenomix.seqslab.piper.operators.format.PartitionedFormat"
                    },
                    "p_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                    },
                },
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-all-single",
                "description": "File-based (BAM) workload without data parallelization",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "",
                            "class": "",
                            "parallelism": "",
                            "select-type": "All",
                            "disable-SV-Dup": True,
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-10-13",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-grch38-155",
                "description": "File-based (BAM) workload parallelization pipeline with the GRCh38 reference genome parallelized into 155 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/38/GRCH/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/38/contiguous_unmasked_regions_155_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-grch38-3101",
                "description": "File-based (BAM) workload parallelization pipeline with the hg19 reference genome parallelized into 3,101 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/38/GRCH/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/38/contiguous_unmasked_regions_3101_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-grch38-50",
                "description": "File-based (BAM) workload parallelization pipeline with the GRCh38 reference genome parallelized into 50 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/38/GRCH/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/38/contiguous_unmasked_regions_50_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-grch38-chromosomes",
                "description": "File-based (BAM) workload parallelization pipeline with each GRCh38 chromosome in a separate partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/38/GRCH/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/38/chromosomes",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-grch38-single",
                "description": "File-based (BAM) workload with records of all GRCh38 primary contigs in a single partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/38/GRCH/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/38/single_node_workflow",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-hg19-155",
                "description": "File-based (BAM) workload parallelization pipeline with the hg19 reference genome parallelized into 155 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/contiguous_unmasked_regions_155_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-hg19-3109",
                "description": "File-based (BAM) workload parallelization pipeline with the hg19 reference genome parallelized into 3,109 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/contiguous_unmasked_regions_3109_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-hg19-77",
                "description": "File-based (BAM) workload parallelization pipeline with the hg19 reference genome parallelized into 77 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/contiguous_unmasked_regions_77_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-hg19-chr20-45",
                "description": "File-based (BAM) workload parallelization pipeline with the hg19 reference genome chr20 parallelized into 45 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/contiguous_unmasked_regions_chr20_45_parts",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-hg19-chromosomes",
                "description": "File-based (BAM) workload parallelization pipeline with each hg19 chromosome in a separate partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/chromosomes",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-hg19-single",
                "description": "File-based (BAM) workload with records of all hg19 primary contigs in a single partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/single_node_workflow",
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_bam_partition-unmap-single",
                "description": "File-based (unmapped BAM) workload without data parallelization",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "org.bdgenomics.adam.cli.piper.BamSource",
                    {
                        "name": "org.bdgenomics.adam.cli.piper.BamPartition",
                        "arguments": {
                            "ref": "",
                            "parallelism": "",
                            "select-type": "Unmap",
                            "disable-SV-Dup": True,
                        },
                    },
                    "org.bdgenomics.adam.cli.piper.BamFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-10-13",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_fastq_auto-path",
                "description": "File-based (FASTQ) workload pipeline without data parallelization",
                "file_type": "fastq,fastq.gz,fq.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": {
                    "sink": {
                        "class": "com.atgenomix.seqslab.piper.operators.sink.HadoopSink"
                    },
                    "format": {
                        "class": "com.atgenomix.seqslab.piper.operators.format.PartitionedFormat"
                    },
                    "p_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                    },
                    "collect": {
                        "class": "com.atgenomix.seqslab.piper.operators.collect.LocalCollect"
                    },
                },
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_fastq_partition-1048576_path",
                "description": "File-based (FASTQ) workload parallelization pipeline with 1,048,576 read records in each partition",
                "file_type": "fastq,fastq.gz,fq.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    {
                        "name": "com.atgenomix.seqslab.piper.operators.source.FastqSource",
                        "arguments": {
                            "codec": "org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec"
                        },
                    },
                    {
                        "name": "com.atgenomix.seqslab.piper.operators.partition.FastqPartition",
                        "arguments": {"parallelism": "1048576"},
                    },
                    "com.atgenomix.seqslab.piper.operators.format.FastqFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_fastq_partition-3145728_path",
                "description": "File-based (FASTQ) workload parallelization pipeline with 3,145,728 read records in each partition",
                "file_type": "fastq,fastq.gz,fq.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": {
                    "format": {
                        "class": "com.atgenomix.seqslab.piper.operators.format.FastqFormat"
                    },
                    "p_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                    },
                    "source": {
                        "class": "com.atgenomix.seqslab.piper.operators.source.FastqSource",
                        "codec": "org.seqdoop.hadoop_bam.util.BGZFEnhancedGzipCodec",
                    },
                    "partition": {
                        "class": "com.atgenomix.seqslab.piper.operators.partition.FastqPartition",
                        "parallelism": "3145728",
                    },
                },
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_file_auto",
                "description": "File-based workload pipeline with intrinsic data parallelization",
                "file_type": "*",
                "workload_type": "FILE",
                "input": True,
                "operators": {
                    "sink": {
                        "class": "com.atgenomix.seqslab.piper.operators.sink.HadoopSink"
                    },
                    "c_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.CPipe"
                    },
                    "source": {
                        "class": "com.atgenomix.seqslab.piper.operators.source.PartitionedSource"
                    },
                    "collect": {
                        "class": "com.atgenomix.seqslab.piper.operators.collect.LocalCollect"
                    },
                },
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_file_auto_stdin",
                "description": "File-based workload pipeline with intrinsic data parallelization via stdin",
                "file_type": "*",
                "workload_type": "FILE",
                "input": True,
                "operators": {
                    "sink": {
                        "class": "com.atgenomix.seqslab.piper.operators.sink.HadoopSink"
                    },
                    "c_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.CPipe"
                    },
                    "source": {
                        "class": "com.atgenomix.seqslab.piper.operators.source.PartitionedSource"
                    },
                    "collect": {
                        "class": "com.atgenomix.seqslab.piper.operators.collect.LocalCollect"
                    },
                },
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_generic-singular_auto",
                "description": "Automatic single-partition workload pipeline for input files (e.g., hg19.fa genome reference file), input directories containing multiple files or subdirectories (e.g., genome reference directory), and intermediate datasets of a single file",
                "file_type": "*",
                "workload_type": "DEFAULT",
                "input": True,
                "operators": [
                    "com.atgenomix.seqslab.piper.operators.format.SingularFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_innput_bam_partition_grch38-part23",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the GRCh38 primary chromosome parallelized into 23 partitions (one autosome per partition; chrX, chrY, and chrM merged into a single partition)",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerGRCh38Part23"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_innput_bam_partition_hg19-part23",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the hg19 primary chromosome parallelized into 23 partitions (one autosome per partition; chrX, chrY, and chrM merged into a single partition)",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Part23"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_1",
                "description": "File-based (BAM) workload pipeline with all records in a single partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerPart1"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_1-unmap",
                "description": "File-based (BAM) workload pipeline with unmapped records in a single partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerPart1Unmap"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_grch38-part23",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the GRCh38 primary chromosome parallelized into 23 partitions (one autosome per partition; chrX, chrY, and chrM merged into a single partition)",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerGRCh38Part23"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_grch38-part3101",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the GRCh38 primary chromosome parallelized into 3,101 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerGRCh38Part3101"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_grch38-part50",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the GRCh38 primary chromosome parallelized into 50 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerGRCh38Part50"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_grch38-part50-paired",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the GRCh38 primary chromosome parallelized into 50 contiguous unmasked regions, where both reads in a read pair are presented in each partition for analysis (e.g., read consensus)",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerGRCh38Part50Consensus"],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_hg19-chr20-part45",
                "description": "File-based (BAM) workload parallelization pipeline with the hg19 reference genome chr20 parallelized into 45 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Chr20Part45"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_hg19-part155",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the hg19 primary chromosome parallelized into 155 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Part155"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_hg19-part155-paired",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the hg19 primary chromosome parallelized into 155 contiguous unmasked regions, where both reads in a read pair are presented in each partition for analysis (e.g., read consensus)",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Part155Consensus"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_hg19-part23",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the hg19 primary chromosome parallelized into 23 partitions (one autosome per partition; chrX, chrY, and chrM merged into a single partition)",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Part23"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_hg19-part3109",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the hg19 primary chromosome parallelized into 3,109 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Part3109"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_bam_partition_hg19-part77",
                "description": "File-based (BAM) workload parallelization pipeline with reads on the hg19 primary chromosome parallelized into 77 contiguous unmasked regions",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerHg19Part77"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_fastq_partition_1M",
                "description": "File-based (FASTQ) workload parallelization pipeline with 1,048,576 read records for each partition",
                "file_type": "fastq,fastq.gz,fq.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": ["FastqPartitioner"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_fastq_partition_per-1M-reads",
                "description": "File-based (FASTQ) workload parallelization pipeline with 1,048,576 read records for each partition",
                "file_type": "fastq,fastq.gz,fq.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": ["FastqPartitioner"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_reference",
                "description": "Automatic workload pipeline for sharing files or directories across a cluster environment",
                "file_type": "*",
                "workload_type": "SHARED",
                "input": True,
                "operators": ["RefLoader"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_ubam_partition_1",
                "description": "File-based (BAM) workload with unmapped records in a single partition",
                "file_type": "bam",
                "workload_type": "FILE",
                "input": True,
                "operators": ["BamPartitionerPart1Unmap"],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_vcf_partition_grch38-3101",
                "description": "File-based (VCF) workload parallelization pipeline with the GRCh38 reference genome parallelized into 3,101 contiguous unmasked regions",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "VcfPartitionerGRCh38Part3101",
                    "VcfDataFrameTransformer",
                    "VcfExecutor",
                ],
                "version": "2022-11-22",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_vcf_partition_hg19-3109",
                "description": "File-based (VCF) workload parallelization pipeline with the hg19 reference genome parallelized into 3,109 contiguous unmasked regions",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "VcfPartitionerHg19Part3109",
                    "VcfDataFrameTransformer",
                    "VcfExecutor",
                ],
                "version": "2022-11-22",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_input_vcf_sql-glow",
                "description": "File-based (VCF) workload loading pipeline using Glow and Delta Lake",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": ["VcfGlowTransformer", "TableLocalizationExecutor"],
                "version": "2022-11-22",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_memory_auto",
                "description": "Memory-based workload pipeline with intrinsic data parallelization",
                "file_type": "*",
                "workload_type": "MEMORY",
                "input": True,
                "operators": {
                    "sink": {
                        "class": "com.atgenomix.seqslab.piper.operators.sink.HadoopSink"
                    },
                    "m_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.MPipe"
                    },
                    "source": {
                        "class": "com.atgenomix.seqslab.piper.operators.source.PartitionedSource"
                    },
                    "collect": {
                        "class": "com.atgenomix.seqslab.piper.operators.collect.LocalCollect"
                    },
                },
                "version": "2021-07-18",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_output_generic",
                "description": "Generic output operator pipeline for uploading data",
                "file_type": "*",
                "workload_type": "DEFAULT",
                "input": False,
                "operators": [],
                "version": "2022-11-14",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_partition_auto-path",
                "description": "File-based workload pipeline with intrinsic data parallelization (default operator pipeline configuration in the Atgenomix implementation of Cromwell)",
                "file_type": "*",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "com.atgenomix.seqslab.piper.operators.format.PartitionedFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_shared-dir_auto",
                "description": "Automatic workload pipeline for sharing directories that contain multiple files or subdirectories across a cluster environment",
                "file_type": "*",
                "workload_type": "SHARED",
                "input": True,
                "operators": [
                    "com.atgenomix.seqslab.piper.operators.format.SharedDir",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_shared-file_auto",
                "description": "Automatic workload pipeline for sharing files (e.g., genome reference file) across a cluster environment",
                "file_type": "*",
                "workload_type": "SHARED",
                "input": True,
                "operators": [
                    "com.atgenomix.seqslab.piper.operators.format.SharedFile",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_vcf_partition-grch38-3101",
                "description": "File-based (VCF) workload parallelization pipeline with the GRCh38 reference genome parallelized into 3,101 contiguous unmasked regions",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "VcfPartitionerGRCh38Part3101",
                    "VcfDataFrameTransformer",
                    "VcfExecutor",
                ],
                "version": "2022-11-22",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_vcf_partition-grch38-single",
                "description": "File-based (VCF) workload with records of all GRCh38 primary contigs in a single partition",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "com.atgenomix.seqslab.piper.operators.source.VcfSource",
                    {
                        "name": "com.atgenomix.seqslab.piper.operators.partition.VcfPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/38/GRCH/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/38/single_node_workflow",
                        },
                    },
                    "com.atgenomix.seqslab.piper.operators.format.VcfFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_vcf_partition-hg19-3109",
                "description": "File-based (VCF) workload parallelization pipeline with the hg19 reference genome parallelized into 3,109 contiguous unmasked regions",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "VcfPartitionerHg19Part3109",
                    "VcfDataFrameTransformer",
                    "VcfExecutor",
                ],
                "version": "2022-11-22",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_vcf_partition-hg19-chromosomes",
                "description": "File-based (VCF) workload parallelization pipeline with each hg19 chromosome in a separate partition",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": {
                    "sink": {
                        "class": "com.atgenomix.seqslab.piper.operators.sink.HadoopSink"
                    },
                    "format": {
                        "class": "com.atgenomix.seqslab.piper.operators.format.VcfFormat"
                    },
                    "p_pipe": {
                        "class": "com.atgenomix.seqslab.piper.operators.pipe.PPipe"
                    },
                    "source": {
                        "class": "com.atgenomix.seqslab.piper.operators.source.VcfSource"
                    },
                    "collect": {
                        "class": "com.atgenomix.seqslab.piper.operators.collect.LocalCollect"
                    },
                    "partition": {
                        "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                        "class": "com.atgenomix.seqslab.piper.operators.partition.VcfPartition",
                        "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/chromosomes",
                    },
                },
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_vcf_partition-hg19-single",
                "description": "File-based (VCF) workload with records of all hg19 primary contigs in a single partition",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": [
                    "com.atgenomix.seqslab.piper.operators.source.VcfSource",
                    {
                        "name": "com.atgenomix.seqslab.piper.operators.partition.VcfPartition",
                        "arguments": {
                            "ref": "wasbs://static@seqslabbundles.blob.core.windows.net/reference/19/HG/ref.dict",
                            "parallelism": "wasbs://static@seqslabbundles.blob.core.windows.net/system/bed/19/single_node_workflow",
                        },
                    },
                    "com.atgenomix.seqslab.piper.operators.format.VcfFormat",
                    "com.atgenomix.seqslab.piper.operators.pipe.PPipe",
                ],
                "version": "2022-03-07",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
            {
                "id": "opp_vcf_sql-glow",
                "description": "File-based (VCF) workload loading pipeline using Glow and Delta Lake",
                "file_type": "vcf,gvcf,vcf.gz,gvcf.gz",
                "workload_type": "FILE",
                "input": True,
                "operators": ["VcfGlowTransformer", "TableLocalizationExecutor"],
                "version": "2022-11-22",
                "cus_id": "cus_P7VOS8Hn6l4X1m2",
            },
        ],
        "calls": {
            "GATK-Germline-Snps-Indels/wdl/GATK-Germline-Snps-Indels-main.wdl": {
                "PreProcessingForVariantDiscovery_GATK4": [
                    "PreProcessingForVariantDiscovery_GATK4"
                ],
                "HaplotypeCallerGvcf_GATK4": ["HaplotypeCallerGvcf_GATK4"],
                "IndexBam": ["IndexBam"],
                "IndexVcf": ["IndexVcf"],
            },
            "GATK-Germline-Snps-Indels/wdl/subworkflows/haplotypecaller-gvcf-gatk4.wdl": {
                "HaplotypeCaller": ["HaplotypeCaller"]
            },
            "GATK-Germline-Snps-Indels/wdl/subworkflows/processing-for-variant-discovery-gatk4.wdl": {
                "Fastp": ["Fastp"],
                "BwaMem": ["BwaMem"],
                "MarkDuplicates": ["MarkDuplicates"],
                "SortAndFixTags": ["SortAndFixTags"],
                "BaseRecalibrator": ["BaseRecalibrator"],
                "ApplyBQSR": ["ApplyBQSR"],
            },
            "GATK-Germline-Snps-Indels/wdl/subworkflows/tasks.wdl": {},
        },
        "inputs": {
            "GermlineSnpsIndelsGatk4.maxMemForGATK": "Int (optional, default = 6)",
            "GermlineSnpsIndelsGatk4.makeBamout": "Boolean (optional, default = false)",
            "GermlineSnpsIndelsGatk4.IndexBam.dockerImage": 'String (optional, default = "atgenomix.azurecr.io/atgenomix/seqslab_runtime-1.4_ubuntu-18.04_preprocessgatk4-4.2.0.0")',
            "GermlineSnpsIndelsGatk4.gatk_path": "String",
            "GermlineSnpsIndelsGatk4.knownIndelsSitesIdxs": "Array[File]",
            "GermlineSnpsIndelsGatk4.refFa": "File",
            "GermlineSnpsIndelsGatk4.refFai": "File",
            "GermlineSnpsIndelsGatk4.refSa": "File",
            "GermlineSnpsIndelsGatk4.inFileFqs": "Array[File]",
            "GermlineSnpsIndelsGatk4.dbsnpVCFTbi": "File",
            "GermlineSnpsIndelsGatk4.makeGVCF": "Boolean (optional, default = false)",
            "GermlineSnpsIndelsGatk4.refAmb": "File",
            "GermlineSnpsIndelsGatk4.refName": "String",
            "GermlineSnpsIndelsGatk4.bwaCommandline": 'String (optional, default = "bwa mem -K 100000000 -v 3 -t 16 -Y $bash_ref_fasta")',
            "GermlineSnpsIndelsGatk4.refAnn": "File",
            "GermlineSnpsIndelsGatk4.refDict": "File",
            "GermlineSnpsIndelsGatk4.IndexVcf.dockerImage": 'String (optional, default = "atgenomix.azurecr.io/atgenomix/seqslab_runtime-1.4_ubuntu-18.04_preprocessgatk4-4.2.0.0")',
            "GermlineSnpsIndelsGatk4.sampleName": "String",
            "GermlineSnpsIndelsGatk4.gotc_path": "String",
            "GermlineSnpsIndelsGatk4.refPac": "File",
            "GermlineSnpsIndelsGatk4.dbsnpVCF": "File",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ref_alt": "File? (optional)",
            "GermlineSnpsIndelsGatk4.refBwt": "File",
            "GermlineSnpsIndelsGatk4.knownIndelsSitesVCFs": "Array[File]",
        },
        "i_configs": {
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.input_bam": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.ref_dict": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.ref_fasta": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.ref_fasta_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.IndexBam.inFileBam": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.IndexVcf.inFileVCF": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.input_bam": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.input_bam_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.recalibration_report": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.ref_dict": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.ref_fasta": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.ref_fasta_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.dbSNP_vcf": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.dbSNP_vcf_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.input_bam": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.input_bam_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.known_indels_sites_VCFs": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.known_indels_sites_indices": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.ref_dict": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.ref_fasta": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.ref_fasta_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.inFileFastqR1": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.inFileFastqR2": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_alt": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_amb": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_ann": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_bwt": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_dict": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_fasta": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_fasta_index": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_pac": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.ref_sa": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.Fastp.inFileFastqR1": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.Fastp.inFileFastqR2": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.MarkDuplicates.input_bam": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.input_bam": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.ref_dict": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.ref_fasta": "opp_generic-singular_auto",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.ref_fasta_index": "opp_generic-singular_auto",
        },
        "o_configs": {
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.bamout": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.output_vcf": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.HaplotypeCallerGvcf_GATK4.HaplotypeCaller.output_vcf_index": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.IndexBam.outFileBai": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.IndexBam.outFileBam": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.IndexVcf.outFileVCF": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.IndexVcf.outFileVCFTbi": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.recalibrated_bam": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.ApplyBQSR.recalibrated_bam_index": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BaseRecalibrator.recalibration_report": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.BwaMem.output_bam": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.Fastp.outFileFastpHtml": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.Fastp.outFileFastpJson": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.Fastp.outFileFastqR1": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.Fastp.outFileFastqR2": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.MarkDuplicates.duplicate_metrics": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.MarkDuplicates.output_bam": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.output_bam": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.output_bam_index": "opp_output_generic",
            "GermlineSnpsIndelsGatk4.PreProcessingForVariantDiscovery_GATK4.SortAndFixTags.output_bam_md5": "opp_output_generic",
        },
        "graph": 'digraph GermlineSnpsIndelsGatk4 {\n  #rankdir=LR;\n  compound=true;\n\n  # Links\n  CALL_HaplotypeCallerGvcf_GATK4 -> CALL_IndexVcf\n  CALL_PreProcessingForVariantDiscovery_GATK4 -> CALL_HaplotypeCallerGvcf_GATK4\n  CALL_PreProcessingForVariantDiscovery_GATK4 -> CALL_IndexBam\n\n  # Nodes\n  CALL_IndexVcf [label="call IndexVcf"]\n  CALL_PreProcessingForVariantDiscovery_GATK4 [label="call PreProcessingForVariantDiscovery_GATK4";shape="oval";peripheries=2]\n  CALL_HaplotypeCallerGvcf_GATK4 [label="call HaplotypeCallerGvcf_GATK4";shape="oval";peripheries=2]\n  CALL_IndexBam [label="call IndexBam"]\n}\n',
    }


class mock_Resource(AzureResource):
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def container_registry(scr_id: str, repositories: List[str], reload: bool) -> dict:
        return {
            "id": "/subscriptions/62fccd52-f6fe-4f3b-aa3a-bfe2b4ae0bbc/resourceGroups/atgxtestws/providers/Microsoft"
            ".ContainerRegistry/registries/atgxtestws62fccacr",
            "name": "atgxtestws62fccacr",
            "location": "westus2",
            "login_server": "atgxtestws62fccacr.azurecr.io",
            "admin_user": True,
            "authorization": "Basic YXRneHRlc3R3czYyZmNjYWNyOnFoMm9vU1R2Uz0wQmt6RVZiakhYbEF2ZFR0MWwzZDZn",
            "repositories": [
                {
                    "name": "atgenomix/seqslab_runtime-1.4_ubuntu-18.04_gatk4",
                    "tags": [
                        {
                            "name": "2022-01-22-07-00",
                            "digest": "sha256:493a88037f22ff1f4454d8977fa95225460fbd4c823e7ad2e65a168b0af854cb",
                            "created": "2022-01-22T07:33:05.6010297Z",
                            "last_updated": "2022-01-22T07:33:05.6010297Z",
                            "size": 3082465110,
                            "type": "docker",
                        },
                        {
                            "name": "2022-01-22-09-45",
                            "digest": "sha256:694fd6c44b792708922403d10b86a44f429f905cc97276fb334afe004b1fb3df",
                            "created": "2022-01-22T11:44:49.7140945Z",
                            "last_updated": "2022-01-22T11:44:49.7140945Z",
                            "size": 3088748536,
                            "type": "docker",
                        },
                        {
                            "name": "2022-01-09-02-00",
                            "digest": "sha256:8117fa6678d846bd11620eb9daeefe85037a5afe4ad920cf552fcbc7c478c6c8",
                            "created": "2022-01-12T03:30:41.0375026Z",
                            "last_updated": "2022-01-12T03:30:41.0375026Z",
                            "size": 3072366309,
                            "type": "docker",
                        },
                        {
                            "name": "2022-01-18-04-14",
                            "digest": "sha256:b4f8c266658b3d3a1e43785b4dc7f4f29e95caa35679d41efb226472660eeb8f",
                            "created": "2022-01-22T01:45:45.0746722Z",
                            "last_updated": "2022-01-22T01:45:45.0746722Z",
                            "size": 3072453965,
                            "type": "docker",
                        },
                        {
                            "name": "2021-12-29-07-28",
                            "digest": "sha256:f6dafa531c4814bc013d5929d93578a2e12ad053f9283c5f1ab78d935395a8fa",
                            "created": "2021-12-29T12:23:55.7253318Z",
                            "last_updated": "2021-12-29T12:23:55.7253318Z",
                            "size": 3071923050,
                            "type": "docker",
                        },
                    ],
                },
                {
                    "name": "atgenomix/seqslab_runtime-1.4_ubuntu-18.04_hicpro",
                    "tags": [
                        {
                            "name": "2021-12-29-07-28",
                            "digest": "sha256:220febcaf664946aaed00fc22007d840416617dd81dc6ac3de736eccdf3d171f",
                            "created": "2021-12-29T08:26:32.5508052Z",
                            "last_updated": "2021-12-29T08:26:32.5508052Z",
                            "size": 3062954586,
                            "type": "docker",
                        },
                        {
                            "name": "2022-01-17-07-36",
                            "digest": "sha256:30e38c21b119266f42ca316b64222f319f7d01d38de48e77d3516080b4c006b2",
                            "created": "2022-01-17T08:01:22.2105367Z",
                            "last_updated": "2022-01-17T08:01:22.2105367Z",
                            "size": 3063710321,
                            "type": "docker",
                        },
                        {
                            "name": "2021-12-17-10-24",
                            "digest": "sha256:39a3ea9fafe8ada7985f1ec80674ad17252b321216a79371dbbfb256397aabfa",
                            "created": "2021-12-17T02:33:59.3956584Z",
                            "last_updated": "2021-12-17T02:33:59.3956584Z",
                            "size": 3029167678,
                            "type": "docker",
                        },
                        {
                            "name": "2022-01-18-04-14",
                            "digest": "sha256:7f53d204fa0bf986edc7a5c2564273f6aa986623239dff92e3670845f23a5e99",
                            "created": "2022-01-26T05:20:26.6844863Z",
                            "last_updated": "2022-01-26T05:20:26.6844863Z",
                            "size": 3062198892,
                            "type": "docker",
                        },
                        {
                            "name": "2022-01-09-02-00",
                            "digest": "sha256:90c6102c57a028127af33f42f7fda17e057badfc1655207fb7bd0cf20709c210",
                            "created": "2022-01-12T03:32:18.5785938Z",
                            "last_updated": "2022-01-12T03:32:18.5785938Z",
                            "size": 3063522956,
                            "type": "docker",
                        },
                    ],
                },
                {
                    "name": "atgenomix/seqslab_runtime-1.4_ubuntu-18.04_iter_mapping",
                    "tags": [
                        {
                            "name": "2022-01-21-11-50",
                            "digest": "sha256:4d066951e4c6551b656f91237a6867309ad11f26b52c860c721bc0a7004a232d",
                            "created": "2022-01-21T08:55:01.0940729Z",
                            "last_updated": "2022-01-21T08:55:01.0940729Z",
                            "size": 2437559017,
                            "type": "docker",
                        }
                    ],
                },
                {
                    "name": "samples/nginx",
                    "tags": [
                        {
                            "name": "latest",
                            "digest": "sha256:57a94fc99816c6aa225678b738ac40d85422e75dbb96115f1bb9b6ed77176166",
                            "created": "2021-08-10T09:52:49.1368541Z",
                            "last_updated": "2021-08-10T09:52:49.1368541Z",
                            "size": 7737579,
                            "type": "docker",
                        }
                    ],
                },
            ],
        }


class mock_TRSregister(AzureTRSregister):
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_tool(data: dict) -> dict:
        return {
            "id": f"{data.get('id')}",
            "toolclass": {"name": "string", "description": "string"},
            "name": "string",
            "description": "string",
            "aliases": {
                "additionalProp1": "string",
                "additionalProp2": "string",
                "additionalProp3": "string",
            },
            "has_checker": True,
            "checker_url": "string",
        }

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_version(data: dict, tool_id: str, workspace: str) -> dict:
        return {
            "images": [
                {
                    "checksum": {
                        "checksum": "57a94fc99816c6aa225678b738ac40d85422e75dbb96115f1bb9b6ed77176166",
                        "type": "sha256",
                    },
                    "image_type": "Docker",
                    "image_name": "samples/nginx",
                    "registry_host": "seqslabapi97e51acr.azurecr.io",
                    "size": 7737579,
                    "updated_time": "2022-02-22T07:23:10.836205Z",
                },
                {
                    "checksum": {
                        "checksum": "57a94fc99816c6aa225678b738ac40d85422e75dbb96115f1bb9b6ed77176157",
                        "type": "sha256",
                    },
                    "image_type": "Docker",
                    "image_name": "samples/nginx4",
                    "registry_host": "seqslabapi97e51acr.azurecr.io",
                    "size": 773757121214214,
                    "updated_time": "2022-02-22T07:23:10.849083Z",
                },
            ],
            "access_url": "https://atgxtestws62fccstorage.dfs.core.windows.net/seqslab/trs/trs_test_NqIlrIzNKp/1.0",
            "descriptor_type": ["WDL"],
            "author": [],
            "name": None,
            "version_id": "1.0",
            "is_production": False,
            "meta_version": "2022-02-22T07:23:10.820474Z",
            "verified": False,
            "verified_source": [],
            "signed": False,
            "included_apps": [],
            "url": "/trs/v2/tools/trs_test_NqIlrIzNKp/versions/1.0/",
        }

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_file(
        data: dict, zip_file: str, tool_id: str, version_id: str, descriptor_type: str
    ) -> str:
        return mock_TRSregister.TRS_TOOLFILE_URL.format(
            tool_id=tool_id,
            version_id=version_id,
            descriptor_type=descriptor_type,
            backend="azure",
        )

    @staticmethod
    def list_tool(page: int, page_size: int):
        return {
            "results": [
                {
                    "id": "trs_iYv6vasXL7mu7Cu",
                    "name": "Seqslab-Hail",
                    "description": "Leverage Hail on Seqslab V3 Platform",
                    "meta_version": "2021-12-14T03:01:37.852139Z",
                    "aliases": {},
                    "organization": "cus_Hy8DlcOkaSItHwm",
                    "toolclass": {
                        "id": 3,
                        "name": "InteractiveNotebook",
                        "description": "InteractiveNotebook",
                    },
                    "has_checker": True,
                    "checker_url": "https://github.com/hail-is/hail",
                    "url": "http://dev-api.seqslab.net/trs/v2/tools/trs_iYv6vasXL7mu7Cu/",
                }
            ]
        }

    @staticmethod
    def list_version(tool_id: str):
        return {
            "results": [
                {
                    "images": [
                        {
                            "checksum": {
                                "checksum": "56656d521a88764cba1e3965a1bbba8699f91544017efe59af26703b18605da8",
                                "type": "sha256",
                            },
                            "image_type": "Docker",
                            "image_name": "atgenomix/seqslab_runtime-1.3_ubuntu-18.04_hail-annotation:latest",
                            "registry_host": "atgenomix.azurecr.io",
                            "size": 0,
                            "updated_time": "2021-12-14T03:01:39.062798Z",
                        }
                    ],
                    "access_url": "https://atgxtestws62fccstorage.dfs.core.windows.net/seqslab/trs"
                    "/trs_iYv6vasXL7mu7Cu/1.0",
                    "descriptor_type": ["JNB"],
                    "author": {},
                    "name": "Seqslab-Hail",
                    "version_id": "1.0",
                    "is_production": True,
                    "meta_version": "2021-12-14T03:01:39.042726Z",
                    "verified": True,
                    "verified_source": {},
                    "signed": True,
                    "included_apps": {},
                    "url": "http://dev-api.seqslab.net/trs/v2/tools/trs_iYv6vasXL7mu7Cu/versions/1.0/",
                }
            ]
        }

    @staticmethod
    def delete_version(tid: str, vid: str):
        return b""

    @staticmethod
    def delete_tool(tid: str):
        return b""

    @staticmethod
    def get_file(
        tool_id: str, version_id: str, download_path: str, descriptor_type: str
    ):
        return 200


class mock_Tools(BaseTools):
    """Mock register commands"""

    def __init__(self):
        pass


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


@resource_workspace_patch
class CommandSpecTest(TestCase):
    def setUp(self) -> None:
        self.trs_id = "trs_test_4QLix7cSvY"
        self.trs_version = "1.0"
        self.descriptor_type = "WDL"
        self.workspace = "atgxtestws"
        self.working_dir = f"{dirname(abspath(__file__))}/working-dir/"

    @staticmethod
    def _make_name():
        return "test_tool" + "".join(
            random.choices(string.ascii_letters + string.digits, k=5)
        )

    @patch("seqslab.trs.register.azure.AzureTRSregister", mock_TRSregister)
    def test_command_trs_tool(self):
        tool = mock_Tools()
        tool_name = self._make_name()
        shell = TestShell(commands=[tool.tool])
        value = shell.run_cli_line(
            f"test_shell tool --name {tool_name} --id {self.trs_id}"
        )
        self.assertEqual(0, value)

    @patch("seqslab.trs.register.azure.AzureTRSregister", mock_TRSregister)
    def test_command_trs_version(self):
        tool = mock_Tools()
        version_name = self._make_name()
        images = [
            {
                "registry_host": "seqslabapi97e51acr.azurecr.io",
                "image_name": "samples/nginx",
                "size": 7737579,
                "checksum": "sha256:57a94fc99816c6aa225678b738ac40d85422e75dbb96115f1bb9b6ed77176166",
                "image_type": "Docker",
            },
            {
                "registry_host": "seqslabapi97e51acr.azurecr.io",
                "image_name": "samples/nginx4",
                "size": 773757121214214,
                "checksum": "sha256:57a94fc99816c6aa225678b738ac40d85422e75dbb96115f1bb9b6ed77176157",
                "image_type": "Docker",
            },
        ]
        shell = TestShell(commands=[tool.version])
        value = shell.run_cli_line(
            f"test_shell version --workspace {self.workspace} --name {version_name} --tool-id {self.trs_id} "
            f"--descriptor-type {self.descriptor_type} --id {self.trs_version} "
            f'--images {json.dumps(images).replace(" ", "")}'
        )
        self.assertEqual(0, value)

    @patch("seqslab.trs.register.azure.AzureTRSregister", mock_TRSregister)
    def test_command_trs_file(self):
        tool = mock_Tools()
        shell = TestShell(commands=[tool.file])
        value = shell.run_cli_line(
            f"test_shell file --tool-id {self.trs_id} --version-id {self.trs_version} "
            f"--descriptor-type {self.descriptor_type} --working-dir {self.working_dir} "
            f"--file-info execs/execs.json"
        )
        self.assertEqual(0, value)

    @patch("seqslab.trs.resource.azure.AzureResource", mock_Resource)
    def test_command_trs_images(self):
        tool = mock_Tools()
        shell = TestShell(commands=[tool.images])
        value = shell.run_cli_line(
            "test_shell images --scr-id -1 --repositories runtime/base runtime/base-r"
        )
        self.assertEqual(0, value)

    @patch("seqslab.wes.commands.BaseJobs.parameter", mock_parameter)
    @patch("seqslab.trs.resource.azure.AzureResource", mock_Resource)
    def test_command_trs_execs(self):
        tool = mock_Tools()
        shell = TestShell(commands=[tool.execs])
        value = shell.run_cli_line(
            f"test_shell execs --working-dir {self.working_dir} --main-wdl wdl/main.wdl "
            f"--inputs inputs.json --output execs/execs.json"
        )
        self.assertEqual(0, value)

    @patch("seqslab.trs.register.azure.AzureTRSregister", mock_TRSregister)
    def test_command_trs_list(self):
        tool = mock_Tools()
        shell = TestShell(commands=[tool.list])
        value = shell.run_cli_line("test_shell list")
        self.assertEqual(0, value)
        value = shell.run_cli_line("test_shell list --tool-id test --page 1")
        self.assertEqual(0, value)
        value = shell.run_cli_line("test_shell list --tool-id test")
        self.assertEqual(0, value)

    @patch("seqslab.trs.register.azure.AzureTRSregister", mock_TRSregister)
    def test_command_trs_delete(self):
        tool = mock_Tools()
        shell = TestShell(commands=[tool.delete])
        ## delete version
        value = shell.run_cli_line(
            f"test_shell delete --tool-id {self.trs_id} --version-id {self.trs_version}"
        )
        self.assertEqual(0, value)
        ## delete tool
        value = shell.run_cli_line(f"test_shell delete --tool-id {self.trs_id}")
        self.assertEqual(0, value)

    @patch("seqslab.trs.register.azure.AzureTRSregister", mock_TRSregister)
    def test_command_trs_get(self):
        tool = mock_Tools()
        shell = TestShell(commands=[tool.get])
        value = shell.run_cli_line(
            f"test_shell get --tool-id {self.trs_id} --version-id {self.trs_version} "
            f"--descriptor-type {self.descriptor_type} --download-path {join(self.working_dir, 'download.zip')}"
        )
        self.assertEqual(0, value)


if __name__ == "__main__":
    # main()
    test = CommandSpecTest()
    test.setUp()
    test.test_command_trs_tool()
    test.test_command_trs_execs()
    test.test_command_trs_version()
    test.test_command_trs_file()
    test.test_command_trs_list()
    test.test_command_trs_delete()
    test.test_command_trs_get()
