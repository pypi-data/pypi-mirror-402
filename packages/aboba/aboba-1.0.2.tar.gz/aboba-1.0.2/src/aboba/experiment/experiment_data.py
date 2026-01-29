from dataclasses import field, dataclass
from typing import List

from aboba.base import TestResult


@dataclass
class ExperimentData:
    history: List[TestResult] = field(default_factory=lambda: [])

    def record(self, record: TestResult):
        """

        Add new test result entry

        """
        self.history.append(record)

    def is_empty(self):
        return len(self.history) == 0
