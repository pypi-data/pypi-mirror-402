# Standard Library
import logging
import os
import sys
import tempfile

import seqslab

seqslab_directory = os.path.dirname(os.path.dirname(__file__))


def root_path(path, layer: int):
    assert len(path.split("/")) - 1 > layer, "Layer is too deep."
    dir_path = os.path.dirname(path)
    if layer - 1 > 0:
        dir_path = root_path(dir_path, layer - 1)
    return dir_path


class ProgressBarObject:
    def __init__(
        self,
        total_tasks: int,
        progress_name: str = "Progress",
        bar_length: int = 30,
        log: bool = True,
    ):
        self.progress_name = progress_name
        self.complete_tasks = 0
        self.total_tasks = total_tasks
        self.bar_length = bar_length
        self.percentage = 0
        self.bar_cnt = 0
        self.clocker = 0
        self.spinner = ["|", "/", "-", "\\"]
        if log:
            _path = seqslab.LOGGING["DIR_PATH"]
            if not os.path.exists(_path):
                _path = f"{root_path(__file__, 2)}/log"
                if not os.path.exists(_path):
                    os.mkdir(_path)
            fileobj = tempfile.NamedTemporaryFile(
                mode="w+", prefix="seqslab-cli-progress-", dir=_path, delete=False
            )
            self.logger = logging.getLogger(fileobj.name)
            self.logger.setLevel(logging.DEBUG)
            handler = logging.FileHandler(fileobj.name, "w", "utf-8")
            self.logger.addHandler(handler)
        else:
            self.logger = None

    @staticmethod
    def __bar_string_format(
        spinner: str,
        progress_name: str,
        bar: str,
        space: str,
        percentage: int,
        complete_tasks: int,
        total_tasks: int,
    ) -> str:
        return f"{spinner} {progress_name}: [{bar}{space}] {percentage:.2%} {complete_tasks}/{total_tasks}"

    def update(self, complete_tasks) -> str:
        if self.total_tasks != 0:
            self.complete_tasks = complete_tasks
            self.percentage = self.complete_tasks / self.total_tasks
            self.bar_cnt = int(self.percentage * self.bar_length)
            progress = self.__bar_string_format(
                self.spinner[self.clocker],
                self.progress_name,
                "█" * self.bar_cnt,
                " " * (self.bar_length - self.bar_cnt),
                self.percentage,
                self.complete_tasks,
                self.total_tasks,
            )
            if self.clocker == 3:
                self.clocker = -1
            self.clocker += 1
            return progress
        else:
            return self.__bar_string_format(
                self.spinner[0], self.progress_name, "█" * 1, " " * 0, 1, 0, 0
            )

    def print(self, content: str = "") -> None:
        msg = self.update(self.complete_tasks)
        if len(content):
            msg += f" {content.ljust(200)} "
        sys.stderr.write(f"\r {msg[:100]}")
        sys.stderr.flush()
        sys.stderr.write("")
        sys.stderr.flush()
        if self.logger:
            self.logger.info(msg)

    @staticmethod
    def end() -> None:
        sys.stderr.write("\n")
        sys.stderr.flush()
