
from typing import List, Optional
from typing import Optional, Union, List
from dataclasses import dataclass, field, asdict


INITIAL_KEY_MAP = {
    # Maps 'run_id' from initial load to 'build_run_id'
    "run_id": "build_run_id",
}

TESTCASE_KEY_MAP = {
    # Maps 'run_id' from testcase updates to 'testcase_run_id'
    "run_id": "testcase_run_id",
}


@dataclass
class TestCase:
    testcase: str
    status: str
    started_at: str
    completed_at: Optional[str] = None


@dataclass
class TestResult:
    hash: Optional[str] = None
    type: Optional[str] = None
    author: Optional[str] = None
    testcase_run_id: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    draft: Optional[bool] = None
    build_run_id: Optional[str] = None
    pull_request: Optional[Union[int, str]] = None
    label: Optional[str] = None
    created_at: Optional[str] = None
    built_at: Optional[str] = None
    build_status: Optional[str] = None
    docker_tag: Optional[str] = None
    build_started_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    testcases: List[TestCase] = field(default_factory=list)
    overall_status: Optional[str] = "running"

    def to_json(self):
        """Converts the TestResult instance and its TestCase instances to a JSON-serializable dictionary."""
        result_dict = asdict(self)  # Convert the TestResult instance to a dict
        # Convert each TestCase to a dict
        result_dict['testcases'] = [asdict(tc) for tc in self.testcases]
        return result_dict

    def load_from_builds(self, json_data: dict):
        """Updates the instance with build data."""
        self._update_from_json(json_data, INITIAL_KEY_MAP)

    def load_from_testruns(self, json_data: dict):
        """Updates the instance with test run data, including handling of 'testcases'."""
        self._update_from_json(
            json_data, TESTCASE_KEY_MAP, handle_testcases=True)

    def _update_from_json(self, json_data: dict, key_map: dict, handle_testcases: bool = False):
        """Generic update logic with key mapping and optional testcase handling."""
        for key, value in json_data.items():
            if value is None:
                continue  # Skip null values to avoid overwriting

            mapped_key = key_map.get(key, key)

            if handle_testcases and mapped_key == 'testcases':
                # Uniquely update or append test cases
                updated_testcases = {tc.testcase: tc for tc in self.testcases}
                for testcase_data in value:
                    testcase = TestCase(**testcase_data)
                    updated_testcases[testcase.testcase] = testcase
                self.testcases = list(updated_testcases.values())
            elif hasattr(self, mapped_key):
                current_value = getattr(self, mapped_key)
                # Only update if the current value is None or handling testcases
                if current_value is None or handle_testcases:
                    setattr(self, mapped_key, value)
