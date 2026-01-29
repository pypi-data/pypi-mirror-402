# Standard Library
import asyncio
import io
import os
from functools import lru_cache
from os.path import abspath, dirname
from typing import List, NoReturn
from unittest import TestCase
from unittest.mock import patch

import requests
from seqslab.drs.api.azure import AzureDRSregister
from seqslab.drs.commands import BaseDatahub
from seqslab.drs.storage.azure import BlobStorage
from seqslab.tests.util import TestShell
from seqslab.workspace.commands import BaseWorkspace
from tenacity import retry, stop_after_attempt, wait_fixed
from yarl import URL


async def mock_drs_exact_search(names: List[str], labels: List[str], **kwargs) -> dict:
    return {
        "objects": [
            {
                "id": "drs_lw5rvMjltsMN1Eb",
                "name": "all.zip",
                "self_uri": "drs://dev-api.seqslab.net/drs_aqaynlKB7mDSJKV",
                "size": 9277,
                "created_time": "2022-02-20T13:33:09.129376Z",
                "updated_time": "2022-02-20T13:33:09.129376Z",
                "version": "2022-02-21T05:41:49.633329Z",
                "mime_type": "application/octet-stream",
                "file_type": "zip",
                "description": None,
                "aliases": [],
                "metadata": {
                    "sample": {"host": None, "specimen": None, "phenotype": None},
                    "sequence": {
                        "library": {"name": None, "layout": None, "strategy": None},
                        "quality": {
                            "gtFP": None,
                            "score": None,
                            "fscore": None,
                            "method": None,
                            "recall": None,
                            "queryFP": None,
                            "queryTP": None,
                            "truthFN": None,
                            "truthTP": None,
                            "precision": None,
                        },
                        "platform": {"udi": None, "model": None},
                        "readCount": None,
                        "readCoverage": None,
                        "referenceSeq": {"url": None, "genomeBuild": None},
                    },
                    "investigation": {
                        "center": None,
                        "project": None,
                        "internalReviewBoard": None,
                    },
                },
                "tags": ["andy"],
            }
        ]
    }


async def mock_drs_keyword_search(
    keywords: List[str], labels: List[str], **kwargs
) -> dict:
    return {
        "count": 1,
        "next": "http://api.seqslab.net/ga4gh/drs/v1/objects/?file_types=fastq.gz&label=TPMIC%E8%8F%8C%E7%9B%B8%E8%B3"
        "%87%E6%96%99&page=24&page_size=2",
        "previous": "http://api.seqslab.net/ga4gh/drs/v1/objects/?file_types=fastq.gz&label=TPMIC%E8%8F%8C%E7%9B%B8%E8"
        "%B3%87%E6%96%99&page=22&page_size=2",
        "results": [
            {
                "id": "drs_FecqZUTpYpxFNkq",
                "name": "test_Fg_R2",
                "mime_type": "application/gzip",
                "file_type": "fq.gz",
                "description": None,
                "self_uri": "drs://api.seqslab.net/drs_FecqZUTpYpxFNkq",
                "size": 2328998660,
                "version": "2025-05-06T10:55:55.746480Z",
                "created_time": "2025-05-06T10:49:21.300000Z",
                "updated_time": "2025-05-06T10:49:21.300000Z",
                "deleted_time": None,
                "metadata": {},
                "aliases": [],
                "tags": [],
                "access_methods": [
                    {
                        "id": 6845,
                        "type": "abfss",
                        "region": "westus2",
                        "access_url": {
                            "headers": {
                                "Authorization": "st=2025-05-24T02%3A51%3A38Z&se=2025-05-27T02%3A51"
                                "%3A38Z&sp=rle&spr=https&sv=2023-01-03&sr=c&sig=00xxx123"
                            },
                            "url": "abfss://org-dev@devstorage.dfs.core.windows.net/drs/usr_tSoybvWdMfxtmet"
                            "/uuid/test_Fg_R2.fq.gz",
                        },
                    }
                ],
                "checksums": [],
                "username": "dev.viewer",
                "seqslabsas": [],
            }
        ],
    }


async def mock_drs_crud(
    drs_id: str, method: str, sem: asyncio.Semaphore, **kwargs
) -> dict or NoReturn:
    if method == "delete":
        return None
    else:
        return [
            {
                "id": "drs_lw5rvMjltsMN1Eb",
                "name": "all.zip",
                "mime_type": "application/octet-stream",
                "file_type": "zip",
                "description": None,
                "self_uri": "drs://dev-api.seqslab.net/drs_lw5rvMjltsMN1Eb",
                "size": 9277,
                "version": "2022-02-21T10:01:05.102849Z",
                "created_time": "2022-02-20T13:33:09.129376Z",
                "updated_time": "2022-02-20T13:33:09.129376Z",
                "metadata": {
                    "investigation": {
                        "center": None,
                        "internalReviewBoard": None,
                        "project": None,
                    },
                    "sample": {"specimen": None, "host": None, "phenotype": None},
                    "sequence": {
                        "readCoverage": None,
                        "readCount": None,
                        "library": {"name": None, "strategy": None, "layout": None},
                        "platform": {"model": None, "udi": None},
                        "referenceSeq": {"genomeBuild": None, "url": None},
                        "quality": {
                            "score": None,
                            "method": None,
                            "truthTP": None,
                            "queryTP": None,
                            "truthFN": None,
                            "queryFP": None,
                            "gtFP": None,
                            "precision": None,
                            "recall": None,
                            "fscore": None,
                        },
                    },
                },
                "aliases": [],
                "tags": [],
                "checksums": [
                    {
                        "type": "sha256",
                        "checksum": "598ad6f0c6130fb506a530d006f6cfe970c13e1a8aee76881ec2191704fe83b1",
                    }
                ],
                "access_methods": [
                    {
                        "type": "https",
                        "region": "westus",
                        "access_tier": "Hot",
                        "access_url": {
                            "headers": {},
                            "url": "https://atgxtestws62fccstorage.blob.core.windows.net/seqslab/drs/usr_0iDOO3rOr5Q7503/all.zip",
                        },
                        "access_id": 5480,
                    }
                ],
            }
        ]


def register_json() -> io.StringIO:
    stdin = """
    [
    {
        "name": "reference.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 179200,
        "created_time": "2022-03-16T03:06:47.137043",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/reference.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/reference.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "0c0aa4431bfd85e4a2ef51d93f901879fa91a9a73ae8cbf97b5c6e3a506763f4",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null,
        "deleted_time": "2024-01-04"
    },
    {
        "name": "repeat_mask.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 44800,
        "created_time": "2022-03-16T03:06:50.342819",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/repeat_mask.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/repeat_mask.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "83e3a378d982f2eb58920deabe073501dcd8bca293224e4639d6a7094e8e16c7",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table_stats.txt",
        "mime_type": "application/octet-stream",
        "file_type": "txt",
        "size": 5756,
        "created_time": "2022-03-16T03:06:52.329937",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table_stats.txt",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table_stats.txt",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "76a8db58916053c6ca821ff623d8c91b880889a97d5a9281e2895d5a5c2dd45e",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table.cfg",
        "mime_type": "application/octet-stream",
        "file_type": "cfg",
        "size": 2006,
        "created_time": "2022-03-16T03:06:54.265801",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "3d6ad2bf70c02854b7667ebd217054d5809e4db271dcfed2ee45c9548f42247d",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "NC_045512.2.fa",
        "mime_type": "text/x-fasta",
        "file_type": "fa",
        "size": 30775,
        "created_time": "2022-03-16T03:06:56.289150",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "291c505e14536104cbdebdb6ac70414552505e6a0ea2e7d5ac562f9a3abc791b",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "ref_index.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 5632,
        "created_time": "2022-03-16T03:06:58.200130",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/ref_index.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/ref_index.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "b28c23c86e290229262919695d33089d446cf37dfc9a5482f7ab7cf9f88364d2",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "NC_045512.2.fa.fai",
        "mime_type": "application/octet-stream",
        "file_type": "fai",
        "size": 27,
        "created_time": "2022-03-16T03:07:00.009024",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa.fai",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa.fai",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "33e8c3ccab53ed4fbfa166d5fb4cbd2cc1e725ed07fb29c9e5d5e3950be31d5a",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "NC_045512.2.dict",
        "mime_type": "application/octet-stream",
        "file_type": "dict",
        "size": 103,
        "created_time": "2022-03-16T03:07:01.730970",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.dict",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.dict",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "57b92eac491a91d2e0bc820d346767fb4c34bddb15ca7b2db48d7fc77ca2ca44",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table.cfg.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 954,
        "created_time": "2022-03-16T03:07:03.553585",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "70f19ff2f23a7ab373e966476445885d3f1d2f459bbc25ef2d594e74536c6ac7",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table.cmp",
        "mime_type": "application/octet-stream",
        "file_type": "cmp",
        "size": 97538,
        "created_time": "2022-03-16T03:07:05.401340",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cmp",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cmp",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "11402dee86259746789c2bf68615d400390db7597aab662fbf4b91b5ea0389b0",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "str_table.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 640,
        "created_time": "2022-03-16T03:07:07.150105",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/str_table.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/str_table.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "e5fb402b08c8f1fade6904a8244becdca4664f0daeedb949a8aa9c3398784e71",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    }
]
    """
    return io.StringIO(stdin)


def register_json_no_checksum() -> io.StringIO:
    stdin = """
    [
    {
        "name": "reference.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 179200,
        "created_time": "2022-03-16T03:06:47.137043",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/reference.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/reference.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "repeat_mask.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 44800,
        "created_time": "2022-03-16T03:06:50.342819",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/repeat_mask.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/repeat_mask.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "83e3a378d982f2eb58920deabe073501dcd8bca293224e4639d6a7094e8e16c7",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table_stats.txt",
        "mime_type": "application/octet-stream",
        "file_type": "txt",
        "size": 5756,
        "created_time": "2022-03-16T03:06:52.329937",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table_stats.txt",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table_stats.txt",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "76a8db58916053c6ca821ff623d8c91b880889a97d5a9281e2895d5a5c2dd45e",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table.cfg",
        "mime_type": "application/octet-stream",
        "file_type": "cfg",
        "size": 2006,
        "created_time": "2022-03-16T03:06:54.265801",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "3d6ad2bf70c02854b7667ebd217054d5809e4db271dcfed2ee45c9548f42247d",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "NC_045512.2.fa",
        "mime_type": "text/x-fasta",
        "file_type": "fa",
        "size": 30775,
        "created_time": "2022-03-16T03:06:56.289150",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "291c505e14536104cbdebdb6ac70414552505e6a0ea2e7d5ac562f9a3abc791b",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "ref_index.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 5632,
        "created_time": "2022-03-16T03:06:58.200130",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/ref_index.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/ref_index.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "b28c23c86e290229262919695d33089d446cf37dfc9a5482f7ab7cf9f88364d2",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "NC_045512.2.fa.fai",
        "mime_type": "application/octet-stream",
        "file_type": "fai",
        "size": 27,
        "created_time": "2022-03-16T03:07:00.009024",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa.fai",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.fa.fai",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "33e8c3ccab53ed4fbfa166d5fb4cbd2cc1e725ed07fb29c9e5d5e3950be31d5a",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "NC_045512.2.dict",
        "mime_type": "application/octet-stream",
        "file_type": "dict",
        "size": 103,
        "created_time": "2022-03-16T03:07:01.730970",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.dict",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/NC_045512.2.dict",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "57b92eac491a91d2e0bc820d346767fb4c34bddb15ca7b2db48d7fc77ca2ca44",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table.cfg.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 954,
        "created_time": "2022-03-16T03:07:03.553585",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cfg.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "70f19ff2f23a7ab373e966476445885d3f1d2f459bbc25ef2d594e74536c6ac7",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "hash_table.cmp",
        "mime_type": "application/octet-stream",
        "file_type": "cmp",
        "size": 97538,
        "created_time": "2022-03-16T03:07:05.401340",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cmp",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/hash_table.cmp",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "11402dee86259746789c2bf68615d400390db7597aab662fbf4b91b5ea0389b0",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    },
    {
        "name": "str_table.bin",
        "mime_type": "application/octet-stream",
        "file_type": "bin",
        "size": 640,
        "created_time": "2022-03-16T03:07:07.150105",
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": "https://seqslabwu2c11c8storage.blob.core.windows.net/seqslab/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/str_table.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            },
            {
                "type": "abfss",
                "access_url": {
                    "url": "abfss://seqslab@seqslabwu2c11c8storage.dfs.core.windows.net/drs/usr_jhQcVxpdmMUBSw5/yinhung/SARS-CoV2-ref/str_table.bin",
                    "headers": {
                        "Authorization": null
                    }
                },
                "access_tier": "hot",
                "region": "westus2"
            }
        ],
        "checksums": [
            {
                "checksum": "e5fb402b08c8f1fade6904a8244becdca4664f0daeedb949a8aa9c3398784e71",
                "type": "sha256"
            }
        ],
        "status": "complete",
        "exceptions": null,
        "description": null,
        "metadata": {},
        "tags": [],
        "aliases": [],
        "id": null
    }
]
    """
    return io.StringIO(stdin)


class mock_DRSregister(AzureDRSregister):
    def __init__(self, workspace: str = None):
        super(mock_DRSregister, self).__init__(workspace=workspace)
        self.blob_pay_load = [
            {
                "id": "drs_lw5rvMjltsMN1Eb",
                "name": "all.zip",
                "mime_type": "application/octet-stream",
                "file_type": "zip",
                "description": "testing",
                "self_uri": "drs://dev-api.seqslab.net/drs_lw5rvMjltsMN1Eb",
                "size": 9277,
                "version": "2022-02-21T10:01:05.102849Z",
                "created_time": "2022-02-20T13:33:09.129376Z",
                "updated_time": "2022-02-20T13:33:09.129376Z",
                "metadata": {
                    "investigation": {
                        "center": None,
                        "internalReviewBoard": None,
                        "project": None,
                    },
                    "sample": {"specimen": None, "host": None, "phenotype": None},
                    "sequence": {
                        "readCoverage": None,
                        "readCount": None,
                        "library": {"name": None, "strategy": None, "layout": None},
                        "platform": {"model": None, "udi": None},
                        "referenceSeq": {"genomeBuild": None, "url": None},
                        "quality": {
                            "score": None,
                            "method": None,
                            "truthTP": None,
                            "queryTP": None,
                            "truthFN": None,
                            "queryFP": None,
                            "gtFP": None,
                            "precision": None,
                            "recall": None,
                            "fscore": None,
                        },
                    },
                },
                "aliases": [],
                "tags": [],
                "checksums": [
                    {
                        "type": "sha256",
                        "checksum": "598ad6f0c6130fb506a530d006f6cfe970c13e1a8aee76881ec2191704fe83b1",
                    }
                ],
                "access_methods": [
                    {
                        "type": "https",
                        "region": "westus",
                        "access_tier": "Hot",
                        "access_url": {"headers": {}, "url": "https://storage.url"},
                        "access_id": 1234,
                    }
                ],
            }
        ]
        self.bundle_pay_load = [
            {
                "id": "drs_OVtQjO1ro9CyzkH",
                "name": "test_bundle1",
                "mime_type": "application/octet",
                "file_type": "bundle",
                "description": "testing",
                "self_uri": None,
                "size": 9277,
                "version": "2022-06-14T10:44:23.534748Z",
                "created_time": None,
                "updated_time": None,
                "metadata": {
                    "investigation": {
                        "center": None,
                        "internalReviewBoard": None,
                        "project": None,
                    },
                    "sample": {"specimen": None, "host": None, "phenotype": None},
                    "sequence": {
                        "readCoverage": None,
                        "readCount": None,
                        "library": {"name": None, "strategy": None, "layout": None},
                        "platform": {"model": None, "udi": None},
                        "referenceSeq": {"genomeBuild": None, "url": None},
                        "quality": {
                            "score": None,
                            "method": None,
                            "truthTP": None,
                            "queryTP": None,
                            "truthFN": None,
                            "queryFP": None,
                            "gtFP": None,
                            "precision": None,
                            "recall": None,
                            "fscore": None,
                        },
                    },
                },
                "aliases": [],
                "tags": [],
                "checksums": [
                    {
                        "type": "sha256",
                        "checksum": "1cedc77c40c5affb08f2f6aca46e6d6a0aa8697f1b0ef2369a15b1e98e27640a",
                    }
                ],
                "access_methods": None,
            }
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def get_drs(self, drs_id):
        """
        api drs object
        :response: drs object json
        """
        return self.blob_pay_load[0]

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def post_drs(self, data):
        """
        api drs object
        :param: data
        :response: drs object json
        """
        bundle = False
        if isinstance(data, list):
            if data[0]["file_type"] == "bundle":
                bundle = True
        else:
            if data["file_type"] == "bundle":
                bundle = True
        if bundle:
            return self.bundle_pay_load
        else:
            return data

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def patch_drs(self, data, drs_id) -> dict:
        """
        partial update drs object
        :param: data
        :response: drs object json
        """
        return self.blob_pay_load[0]

    @lru_cache(maxsize=16)
    def root_path(self, workspace_name: str) -> str:
        return "https://root_path"


class mock_BlobStorage(BlobStorage):
    def __init__(self, workspace):
        super(mock_BlobStorage, self).__init__(workspace=workspace)

    @lru_cache(maxsize=16)
    def refresh_token(self, uri: URL, **kwargs):
        return {
            "url": f"{str(uri)}",
            "headers": {
                "Authorization": "st=9999-02-23T03%3A00%3A42Z&se=9999-02-23T04%3A00%3A42Z&sp=racwle&spr=https&sv=2020"
                "-06-12&sr=d&sdd=3&sig=D3XkB69gGPqNmbXLYy59X5xwrLLRIKz1brYHhCYlk0k%3D"
            },
        }

    @lru_cache(maxsize=16)
    def get_token(self, path: str, **kwargs) -> dict:
        return {
            "url": f"https://atgxtestws62fccstorage.blob.core.windows.net/seqslab/drs/usr_0iDOO3rOr5Q7503/{path}",
            "headers": {
                "Authorization": "st=9999-02-23T03%3A00%3A42Z&se=9999-02-23T04%3A00%3A42Z&sp=racwle&spr=https&sv=2020"
                "-06-12&sr=d&sdd=3&sig=D3XkB69gGPqNmbXLYy59X5xwrLLRIKz1brYHhCYlk0k%3D"
            },
            "register_url": "abfss://seqslab@atgxtestws62fccstorage.dfs.core.windows.net/drs/usr_0iDOO3rOr5Q7503",
        }

    @lru_cache(maxsize=16)
    def get_block_list(self, uri: URL, **kwargs) -> iter:
        return

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    @lru_cache(maxsize=16)
    def workspace(name) -> dict:
        return {"location": "westus2", "resources": [{"type": "abfss"}]}

    async def put_block(
        self,
        uri: URL,
        data: open,
        position: int,
        size: int,
        base64_message: str,
        md5_check: bool,
        *args,
        **kwargs,
    ) -> int:
        await asyncio.sleep(1)
        return len(data)

    async def put_blocklist(self, uri: URL, block_id: str, *args, **kwargs) -> NoReturn:
        await asyncio.sleep(1)
        return

    @staticmethod
    @lru_cache(maxsize=16)
    async def expand_blob(drs_id, **kwargs) -> List[dict] or requests.HTTPError:
        await asyncio.sleep(1)
        return {
            "self_uri": "drs://localhost:8000/12345",
            "access_url": "https://atgxtestws62fccstorage.blob.core.windows.net/seqslab/drs/usr_0iDOO3rOr5Q7503"
            "/make_hg19.sh",
            "token": {
                "Authorization": "st=2022-03-14T08%3A10%3A58Z&se=2022-03-17T08%3A10%3A58Z&sp=rle&spr=https&sv=2020-06"
                "-12&sr=b&sig=Ha7To%2BUywhRzW8h0cDqc7qjUDaCwCt32gZBIj2PxY1A%3D "
            },
            "checksum": "sha256:29c12002dbbbcf83d56f0418020c4b83a8240b17b7373731525d44c7200bd35c",
            "files": [
                {
                    "size": 3189,
                    "path": "https://atgxtestws62fccstorage.blob.core.windows.net/seqslab/drs/usr_0iDOO3rOr5Q7503"
                    "/make_hg19.sh",
                }
            ],
        }

    async def get_blob(
        self, url: URL, file: str, pos: asyncio.queues, **kwargs
    ) -> None:
        start, end = await pos.get()
        o_fd = os.open(file, os.O_WRONLY | os.O_CREAT)
        os.lseek(o_fd, start, os.SEEK_CUR)
        os.write(o_fd, b"andy")
        os.close(o_fd)
        await asyncio.sleep(1)
        pos.task_done()
        self.buffer[file] = [
            {"length": end - start + 1, "exception": None, "index": start}
        ]


class mock_Datahub(BaseDatahub):
    """Mock Data Hub commands"""

    def __init__(self):
        super(mock_Datahub, self).__init__()


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
        self.workspace = "atgxtestws"
        self.drs_id = "drs_lw5rvMjltsMN1Eb"

    @patch("seqslab.drs.storage.azure.BlobStorage", mock_BlobStorage)
    def test_command_upload(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.upload])
        # dst = relative file path --file_upload
        file_path = f"{dirname(abspath(__file__))}/upload/all.zip"
        value = shell.run_cli_line(
            f"test_shell upload --workspace {self.workspace} --src {file_path} --dst upload/upload/upload/all.zip"
        )
        self.assertEqual(0, value)
        # dst = relative dir path --file_upload
        file_path = f"{dirname(abspath(__file__))}/upload/all.zip"
        value = shell.run_cli_line(
            f"test_shell upload --workspace {self.workspace} --src {file_path} --dst upload/upload/upload/"
        )
        self.assertEqual(0, value)
        # dst = absolute url dir path --folder_upload
        dir_path = f"{dirname(abspath(__file__))}/upload"
        value = shell.run_cli_line(
            f"test_shell upload --workspace {self.workspace} --src {dir_path} --dst upload/upload/upload -r"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.storage.azure.BlobStorage", mock_BlobStorage)
    def test_command_runsheet_upload(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.upload_runsheet])
        # dst = absolute url file path --file_upload
        runsheet_path = f"{dirname(abspath(__file__))}/upload_runsheet/runsheet.csv"
        dq_path = f"{dirname(abspath(__file__))}/upload_runsheet/fq_dir"
        value = shell.run_cli_line(
            f"test_shell upload-runsheet --seq-run-id Date --workspace {self.workspace} --input-dir {dq_path} "
            f"--run-sheet {runsheet_path}"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.storage.azure.BlobStorage", mock_BlobStorage)
    def test_command_runsheet_v2_upload(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.upload_runsheet])
        # dst = absolute url file path --file_upload
        runsheet_path = f"{dirname(abspath(__file__))}/upload_runsheet/runsheetV2.csv"
        dq_path = f"{dirname(abspath(__file__))}/upload_runsheet/fq_dir"
        value = shell.run_cli_line(
            f"test_shell upload-runsheet --seq-run-id RunName --workspace {self.workspace} --input-dir {dq_path} "
            f"--run-sheet {runsheet_path}"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.storage.azure.BlobStorage", mock_BlobStorage)
    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_download(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.download])
        dir_path = f"{dirname(abspath(__file__))}/download/"
        drs_id = "12345"
        value = shell.run_cli_line(
            f"test_shell download --workspace {self.workspace} --id {drs_id} --dst {dir_path} --overwrite"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_file_blob_register(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_blob])
        access_methods = (
            '[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
            '"Authorization":"authorization"}},"access_tier":"hot","region":"westus3"}] '
        )
        value = shell.run_cli_line(
            f"test_shell register-blob file --workspace {self.workspace} --checksum-type sha256 --checksum "
            f"598ad6f0c6130fb506a530d006f6cfe970c13e1a8aee76881ec2191704fe83b1 --mime-type application/octet-stream "
            f"--file-type zip --name all.zip --size 9277 --created-time 2022-02-20T13:33:09.129376 --deleted-time "
            f"2024-01-04 "
            f"--access-methods {access_methods} --description testing"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_file_blob_register_without_checksum(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_blob])
        access_methods = (
            '[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
            '"Authorization":"authorization"}},"access_tier":"hot","region":"westus3"}] '
        )
        value = shell.run_cli_line(
            f"test_shell register-blob file --workspace {self.workspace} "
            f"--mime-type application/octet-stream "
            f"--file-type zip --name all.zip --size 9277 --created-time 2022-02-20T13:33:09.129376 "
            f"--access-methods {access_methods} --description testing"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    @patch("sys.stdin", register_json())
    def test_command_file_blob_register_stdin_mode(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_blob])
        access_methods = (
            '[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
            '"Authorization":"authorization"}},"access_tier":"hot","region":"westus3"}] '
        )
        value = shell.run_cli_line(
            f"test_shell register-blob file --workspace {self.workspace} --access-methods {access_methods} "
            f"--stdin"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    @patch("sys.stdin", register_json_no_checksum())
    def test_command_file_blob_register_stdin_mode_without_checksum(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_blob])
        access_methods = (
            '[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
            '"Authorization":"authorization"}},"access_tier":"hot","region":"westus3"}] '
        )
        value = shell.run_cli_line(
            f"test_shell register-blob file --workspace {self.workspace} --access-methods {access_methods} "
            f"--stdin"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    @patch("sys.stdin", register_json())
    def test_command_dir_blob_register(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_blob])
        access_methods = (
            '[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
            '"Authorization":"authorization"}},"access_tier":"hot","region":"westus3"}] '
        )
        value = shell.run_cli_line(
            f"test_shell register-blob dir --workspace {self.workspace} --access-methods {access_methods} "
            f"--stdin"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    @patch("sys.stdin", register_json_no_checksum())
    def test_command_dir_blob_register_without_checksum(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_blob])
        access_methods = (
            '[{"type":"https","access_url":{"url":"https://storage.url","headers":{'
            '"Authorization":"authorization"}},"access_tier":"hot","region":"westus3"}] '
        )
        value = shell.run_cli_line(
            f"test_shell register-blob dir --workspace {self.workspace} --access-methods {access_methods} "
            f"--stdin"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_bundle_register(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.register_bundle])
        value = shell.run_cli_line(
            f"test_shell register-bundle --workspace {self.workspace} --name test_bundle --drs-id test_blob "
            f"--deleted-time 2024-01-04"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_drs_get(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.get])
        value = shell.run_cli_line(
            f"test_shell get {self.drs_id} --workspace {self.workspace}"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_drs_add_reads(self):
        datahub = mock_Datahub()
        runsheet_path = f"{dirname(abspath(__file__))}/add-reads_runsheet/runsheet.csv"
        shell = TestShell(commands=[datahub.add_reads_runsheet])
        value = shell.run_cli_line(
            f"test_shell add-reads --run-sheet {runsheet_path} --workspace {self.workspace} --seq-run-id Date"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.api.azure.AzureDRSregister", mock_DRSregister)
    def test_command_drs_update(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.update])
        checksum = "598ad6f0c6130fb506a530d006f6cfe970c13e1a8aee76881ec2191704fe83b1"
        updated_time = "2022-02-20T13:33:09.129376Z"
        value = shell.run_cli_line(
            f"test_shell update {self.drs_id} --workspace {self.workspace} --name andy --tags andy2 andy3 "
            f"--updated-time {updated_time} "
            f"--checksum {checksum} --checksum-type sha256 --deleted-time 2024-01-04"
        )
        self.assertEqual(0, value)

    @patch("seqslab.drs.internal.utils.drs_exact_match", mock_drs_exact_search)
    @patch("seqslab.drs.internal.utils.drs_crud", mock_drs_crud)
    def test_command_drs_delete(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.delete])
        value = shell.run_cli_line(f"test_shell delete {self.drs_id} --tags andy")
        self.assertEqual(0, value)

    @patch("seqslab.drs.internal.utils.drs_keyword_search", mock_drs_keyword_search)
    def test_command_drs_search(self):
        datahub = mock_Datahub()
        shell = TestShell(commands=[datahub.search])
        value = shell.run_cli_line(f"test_shell search {self.drs_id} --tags andy")
        self.assertEqual(0, value)


if __name__ == "__main__":
    test = CommandSpecTest()
    test.setUp()
    test.test_command_upload()
    test.test_command_download()
    test.test_command_drs_search()
    test.test_command_drs_delete()
    test.test_command_file_blob_register()
    test.test_command_file_blob_register_stdin_mode()
    test.test_command_file_blob_register_stdin_mode_without_checksum()
    test.test_command_dir_blob_register()
    test.test_command_dir_blob_register_without_checksum()
    test.test_command_bundle_register()
    test.test_command_drs_update()
    test.test_command_drs_get()
    test.test_command_drs_add_reads()
