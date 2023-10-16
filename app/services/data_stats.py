from app.services.helper_service import TestCaseHelper

from typing import Protocol, Dict, Any

class ComputeStats(Protocol):
    def compute(self, data: Dict[str, Any]) -> None:
        pass


class BasicStatsProcessor:
    def compute(self, data: Dict[str, Any]) -> None:
        pass


class AdditionalStatsProcessor:
    def compute(self, combined_data: Dict[str, Any]) -> None:
        TestCaseHelper.assign_revisions(combined_data)
        median_duration = TestCaseHelper.compute_median_commit_durations(combined_data)
        for entry in combined_data:
            # Processing the testcases' stats
            testcases = entry.get('testcases', [])
            for testcase in testcases:
                TestCaseHelper.compute_median_stats(testcase, median_duration)
