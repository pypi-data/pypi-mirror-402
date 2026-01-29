# Standard Library
import csv
from typing import List, Optional

from seqslab.sample_sheet import Sample, SampleSheet, SampleSheetV2

RECOMMENDED_RUN_KEYS: List[str] = ["Run_Name", "Workflow_URL", "Runtimes"]


class Run:
    """A single run from a run sheet.

    This class is built with the keys and values in the ``"[Data]"`` section of
    the run sheet. The required keys are:

        - ``"Run_Name"``
        - ``"Workflow_URL"``
        - ``"Runtimes"``
        - ``"Run_Schedule_ID``

    A run may include multiple samples.  For samples in a Run Sheet, samples with the same Run_Name will be clustered
    as a single run.
    """

    def __init__(
        self,
        samples: List[Sample],
        run_name: str,
        workflow_url: str,
        runtimes: str,
        run_schedule_id: str = None,
    ) -> None:
        self.sample_sheet: Optional[SampleSheet] = None
        self.run_name = run_name
        self.workflow_url = workflow_url
        self.runtimes = runtimes
        self.run_schedule_id = run_schedule_id
        self.samples = []
        if not workflow_url.endswith("/"):
            raise ValueError(
                f"The given workflow_url does not end with a slash - {workflow_url}."
            )

        for s in samples:
            if set(RECOMMENDED_RUN_KEYS).issubset([key for key in s.keys()]):
                if (
                    s.get("Run_Name") == self.run_name
                    and s.get("Workflow_URL") == self.workflow_url
                    and s.get("Runtimes") == self.runtimes
                    and s.get("Run_Schedule_ID") == self.run_schedule_id
                ):
                    self.samples.append(s)

    def to_json(self) -> dict:
        """Return the properties of this :class:`Run` as JSON serializable."""
        return {
            "run_name": self.run_name,
            "workflow_url": self.workflow_url,
            "runtimes": self.runtimes,
            "samples": [{str(x): str(y) for x, y in s.items()} for s in self.samples],
        }

    def __eq__(self, other: object) -> bool:
        """Runs are equal if the following attributes are equal:
        - ``"Run_Name"``
        For Run having a same Run_Name, Workflow_URL and runtime should also be the same
        """
        if not isinstance(other, Sample):
            raise NotImplementedError
        is_equal: bool = (
            self.run_name == other.Run_Name
            and self.workflow_url == other.workflow_url
            and self.runtimes == other.runtimes
            and set(self.samples) == set(other.samples)
        )
        return is_equal

    def __str__(self) -> str:
        """Cast this object to string."""
        return str(self.to_json)


class RunSheet:
    def __init__(
        self,
        path: str,
        seqslab_section: str = "SeqsLabRunSheet",
        seqslab_format: str = "SeqsLabColumnFormat",
        seqslab_sep: str = "#",
    ):
        self.path = path
        self.sample_sheet_type = self._check_sample_sheet_version(path)
        if self.sample_sheet_type == "v1":
            self.SampleSheet = SampleSheet(path)
        elif self.sample_sheet_type == "v2":
            self.SampleSheet = SampleSheetV2(path)
            updates = self.parse_seqslab_runsheet_section(
                seqslab_section, seqslab_format, seqslab_sep
            )
            self.update_samples(updates)

        self._runs = []
        self._parse_run()

    def parse_seqslab_runsheet_section(
        self, section: str, format_key: str, separator: str
    ) -> dict:
        section_content = self.SampleSheet.__getattribute__(section)
        col_format = section_content.get(format_key)
        columns = col_format.split(separator)
        ret = {}
        for key in section_content:
            if key == format_key:
                continue
            values = section_content.get(key).split(separator)
            assert len(values) == len(columns)
            res = {"Sample_ID": key}
            res.update(dict(zip(columns, values)))
            ret[key] = res
        return ret

    def update_samples(self, updates: dict):
        sample_map = {
            sample["Sample_ID"]: sample for sample in self.SampleSheet.samples
        }
        for key, update_data in updates.items():
            if key in sample_map:
                sample_map[key].upsert(update_data)

    @staticmethod
    def _check_sample_sheet_version(path):
        with open(path, "r") as f:
            headers = [
                item
                for row in list(csv.reader(f, skipinitialspace=True))
                for item in row
                if item.startswith("[") and item.endswith("]")
            ]
            if not headers:
                raise ValueError("given sample sheet path does not include header.")

            find_settings = False
            find_data = False
            find_header = False
            find_reads = False
            for hd in headers:
                h = hd.strip("[]")
                if h == "Header":
                    find_header = True
                if h == "Reads":
                    find_reads = True
                if h.endswith("_Data"):
                    find_data = True
                if h.endswith("_Settings"):
                    find_settings = True
            if not find_header or not find_reads:
                raise ValueError(
                    "given sample sheet without required [Header] or [Reads] sections."
                )
            if find_data and find_settings:
                return "v2"
            else:
                return "v1"

    def _parse_run(self) -> None:
        run_name_set = set()
        runs = {}
        for sample in self.SampleSheet.samples:
            rsig = (
                sample.get("Run_Name"),
                sample.get("Workflow_URL"),
                sample.get("Runtimes"),
                sample.get("Run_Schedule_ID"),
            )
            rn = sample.get("Run_Name")
            if rsig in runs and rn in run_name_set:
                runs[rsig].append(sample)
            elif rsig not in runs and rn not in run_name_set:
                runs[rsig] = [sample]
                run_name_set.add(rn)
            else:
                raise RuntimeError(
                    f"Inconsistent run_name/run_name_set {rn}/{run_name_set} and run sig/runs {rsig}/{runs.keys()}"
                )
        for k, v in runs.items():
            self._runs.append(Run(v, k[0], k[1], k[2], k[3]))

    @property
    def runs(self) -> List:
        """Return the samples present in this :class:`SampleSheet`."""
        return self._runs
