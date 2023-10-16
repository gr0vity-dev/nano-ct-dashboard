from app.services.helper_service import DateTimeHelper

from typing import Protocol, Dict, Any, List
import warnings


def safe_convert_to(desired_type, input, key):
    """
    Safely converts a value from a dictionary to the desired type.
    """
    original_value = input.get(key)
    try:
        input[key] = desired_type(original_value)
    except (KeyError, ValueError, TypeError):
        input[key] = original_value


class DataProcessorMixin:

    def merge_to(self, combined_data: Dict[str, Dict[str, Any]]) -> None:
        for hash_key, processed_data_value in self.get_processed_data().items():
            combined_data.setdefault(hash_key, {}).update(processed_data_value)

    @staticmethod
    def get_nested_value(data: Dict[str, Any], nested_key: str) -> Any:
        keys = nested_key.split('.')
        for key in keys:
            if data is not None and key in data:
                data = data[key]
            else:
                return None
        return data

    def _map_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        mapped_data = {}
        for in_key, out_key in self.key_mappings.items():
            value = self.get_nested_value(data, in_key)
            if value is not None:
                mapped_data[out_key] = value
            else:
                warnings.warn(f"Missing input key '{in_key}'")
        return mapped_data





class IProcessor(Protocol):
    def process(self, data: Any) -> None:
        pass

    def get_processed_data(self) -> Dict[str, Any]:
        pass

    def merge_to(self, combined_data: Dict[str, Dict[str, Any]]) -> None:
        pass




class BuildProcessor(DataProcessorMixin):
    key_mappings = {
        "hash": "hash",
        "type": "type",
        "pull_request": "pr_number",
        "label": "label",
        "created_at": "created_at",
        "built_at": "built_at",
        "build_status": "build_status",
        "docker_tag": "docker_tag"
    }

    def __init__(self, repository_url: str, dataset: List[Dict[str, Any]] = None):
        self.REPOSITORY_URL = repository_url
        self.dataset = dataset
        self.processed_data = {}  # To store the processed data

    def process_all(self) -> None:
        """Process dataset."""
        for item in self.dataset:
            self.process(item)

    def process(self, build: Dict[str, Any]) -> None:
        mapped_build = self._map_keys(build)
        hash_value = mapped_build.get("hash")
        build_status = mapped_build.get('build_status')
        mapped_build["hash_url"] = f"{self.REPOSITORY_URL}/commit/{hash_value}"

        if not hash_value:
            warnings.warn("Encountered data without a hash!")
            return

        if build_status not in ['pass', 'fail', 'building']:
            warnings.warn(f"Encountered {build_status} data for hash: {hash_value}", UserWarning)
            return

        self.processed_data[hash_value] = mapped_build

    def get_processed_data(self) -> Dict[str, Any]:
        return self.processed_data


class TestrunProcessor(DataProcessorMixin):
    key_mappings = {
        "hash": "hash",
        "type": "type",
        "pull_request": "pr_number",
        "started_at": "test_started_at",
        "completed_at": "test_completed_at",
        "testcases": "testcases",
        "overall_status": "overall_status"
    }

    def __init__(self, testruns: List[Dict[str, Any]] = None):
        self.testruns = testruns
        self.processed_data = {}  # To store the processed data

    def process_all(self) -> None:
        """Process all testruns."""
        for testrun in self.testruns:
            self.process(testrun)

    def process(self, testrun: Dict[str, Any]) -> None:
        """Process a single testrun."""
        hash_value = testrun.get("hash")
        if not hash_value:
            return

        mapped_testrun = self._map_keys(testrun)
        self._add_custom_testrun_fields(mapped_testrun)
        self.processed_data[hash_value] = mapped_testrun



    def _add_custom_testrun_fields(self, testrun) -> None:
        started_at = testrun.get("test_started_at")
        completed_at = testrun.get("test_completed_at")
        testrun["test_duration"] = DateTimeHelper.compute_test_duration(started_at, completed_at)
        testrun["test_age"] = DateTimeHelper.compute_time_elapsed(started_at)
        safe_convert_to(int, testrun, "pr_number")

        testcases = sorted(testrun.get('testcases', []), key=lambda x: x.get("testcase", ""))
        testrun["testcases"] = testcases
        overall_status = 'PASS'
        fail_count = 0
        pass_count = 0
        for test in testcases:
            started_at = test.get("started_at")
            completed_at = test.get("completed_at")
            test["duration"] = DateTimeHelper.get_duration_in_s(started_at, completed_at)
            if test.get("status") == "PASS":
                pass_count += 1
            else:
                overall_status = "FAIL"
                fail_count += 1

        testrun["test_status"] = overall_status
        testrun["test_count"] = len(testcases)
        testrun["fail_count"] = fail_count
        testrun["pass_count"] = pass_count



    def get_processed_data(self) -> Dict[str, Any]:
        return self.processed_data




class PRInfoProcessor(DataProcessorMixin):
    key_mappings = {
        "html_url": "pr_url",
        "number": "pr_number",
        "title": "pr_title",
        "user.login": "pr_user"
    }

    def __init__(self, dataset: List[Dict[str, Any]] = None):
        self.dataset = dataset
        self.processed_data = {}  # To store the processed data

    def process_all(self) -> None:
        """Process dataset."""
        for key, value in self.dataset.items():
            self.process((key, value))

    def process(self, pr_data: Dict[str, Any]) -> None:
        if not pr_data:
            return
        hash_value = pr_data[0]  # You need to decide how to get hash for PR data if it's different.
        mapped_pr_data = self._map_keys(pr_data[1])
        self._add_custom_mapping_fields(mapped_pr_data)
        self.processed_data[hash_value] = mapped_pr_data

    def _add_custom_mapping_fields(self, pr_data: Dict[str, Any]) -> None:
        pr_url_value = pr_data.get("pr_url")
        if pr_url_value:
            pr_data["diff_url"] = f"{pr_url_value}/files?diff=split&w=0"

    def get_processed_data(self) -> Dict[str, Any]:
        return self.processed_data


