from app.services.helper_service import TestCaseHelper,DateTimeHelper
import warnings
import json


class DataCombiner:

    REPOSITORY_URL = "https://github.com/nanocurrency/nano-node"

    def __init__(self):
        # This can be expanded to decouple the input keys from the resulting keys.
        self.key_mappings = {
            "builds": {
                "hash": "hash",
                "type": "type",
                "pull_request": "pr_number",
                "label": "label",
                "created_at": "created_at",
                "built_at": "built_at",
                "build_status": "build_status",
                "docker_tag": "docker_tag",
            },
            "testruns": {
                "hash": "hash",
                "type": "type",
                "pull_request": "pr_number",
                "started_at": "test_started_at",
                "completed_at": "test_completed_at",
                "testcases": "testcases",
                "overall_status": "overall_status",
            },
            "pr_info": {
                "html_url" : "pr_url",
                "number": "pr_number",
                "title": "pr_title",
                "user.login": "pr_user"
            },
        }

    def get_nested_value(self, data, nested_key):
        """Retrieve the nested value from a dictionary using dotted key notation."""
        # if data is None : return data

        keys = nested_key.split(".")
        temp_data = data
        for key in keys:
            try:
                temp_data = temp_data[key]
            except KeyError:
                return None
        return temp_data


    def combine_data_as_dict(self, builds, testruns, pr_info):
        combined_data = {}

        for build in builds:
            self.process_build(build, combined_data)

        for testrun in testruns:
            self.process_testrun(testrun, combined_data)

        for hash_value, pr_data in pr_info.items():
            self.process_pr_info(hash_value, pr_data, combined_data)

        self.compute_all_stats(combined_data)

        return combined_data

    def combine_data(self, builds, testruns, pr_info):
        combined_data = self.combine_data_as_dict(builds, testruns, pr_info)
        sorted_data = sorted(combined_data.values(), key=lambda x: x.get('built_at', x.get('created_at', '1970-01-01T00:00:00Z')), reverse=True)
        return list(sorted_data)[:100]




    def process_build(self, build, combined_data):
        mapped_build = self._map_keys(build, "builds")
        hash_value = mapped_build.get("hash")
        build_status = mapped_build.get('build_status')
        mapped_build["hash_url"] = f"{self.REPOSITORY_URL}/commit/{hash_value}"

        if not hash_value:
            warnings.warn("Encountered data without a hash!")
            return

        if build_status not in ['pass', 'fail', 'building']:
            warnings.warn(f"Encountered {build_status} data for hash: {hash_value}", UserWarning)
            return

        combined_data[hash_value] = mapped_build

    def process_testrun(self, testrun, combined_data):
        hash_value = testrun.get("hash")
        if not hash_value:
            return

        mapped_testrun = self._map_keys(testrun, "testruns")
        self._add_custom_testrun_fields(testrun.get('testcases', []))
        combined_data.setdefault(hash_value, {}).update(mapped_testrun)

    def _add_custom_testrun_fields(self, testcases):
        for test in testcases:
            started_at = test.get("started_at")
            completed_at = test.get("completed_at")
            test["duration"] = DateTimeHelper.get_duration_in_s(started_at, completed_at)



    def process_pr_info(self, hash_value, pr_data, combined_data):
        if not pr_data : return
        mapped_pr_data = self._map_keys(pr_data, "pr_info")
        self._add_custom_mapping_fields(mapped_pr_data)
        combined_data.setdefault(hash_value, {}).update(mapped_pr_data)


    def _add_custom_mapping_fields(self, pr_data):
        pr_url_value = pr_data.get("pr_url")
        if pr_url_value:
            pr_data["diff_url"] = f"{pr_url_value}/files?diff=split&w=0"


    def compute_all_stats(self, combined_data):
        self.compute_stats(combined_data)
        self.compute_additional_stats(combined_data)
        TestCaseHelper.assign_revisions(combined_data)

    def compute_stats(self, combined_data):
        # Initially compute 'testduration' for all entries in combined_data
        for _, entry in combined_data.items():
            start_time = entry.get('test_started_at')
            end_time = entry.get('test_completed_at')
            if start_time and end_time:
                entry["test_duration"] = DateTimeHelper.compute_test_duration(start_time, end_time)

            if start_time:
                entry["test_age"] = DateTimeHelper.compute_time_elapsed(start_time)

        # Compute the median duration for commit types Depends on DateTimeHelper.compute_test_duration()
        median_duration = TestCaseHelper.compute_commit_median_durations(combined_data)

        for _, entry in combined_data.items():
            # Processing the testcases' stats
            testcases = entry.get('testcases', [])
            for testcase in testcases:
                TestCaseHelper.compute_single_testcase_stats(testcase, median_duration)


    def compute_additional_stats(self, combined_data):
        for _, entry in combined_data.items():
            testcases = entry.get('testcases', [])

            # Initializing stats counters
            test_count = len(testcases)
            fail_count = sum(1 for testcase in testcases if testcase['status'] == 'FAIL')
            pass_count = test_count - fail_count

            # Determine overall test_status
            test_status = 'PASS' if fail_count == 0 and pass_count > 0 else 'FAIL'

            # Update the entry with computed stats
            entry["test_status"] = test_status
            entry["test_count"] = test_count
            entry["fail_count"] = fail_count
            entry["pass_count"] = pass_count


    def _map_keys(self, data, data_type):
        mapped_data = {}
        for input_key, output_key in self.key_mappings[data_type].items():
            value = self.get_nested_value(data, input_key)

            if value is not None:
                mapped_data[output_key] = value
            else:
                warnings.warn(f"Missing input key {input_key} in {data_type}")
        return mapped_data



