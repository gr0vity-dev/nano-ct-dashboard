from app.services.helper_service import TestCaseHelper,DateTimeHelper
import warnings
import json


class DataCombiner:

    def __init__(self):
        # This can be expanded to decouple the input keys from the resulting keys.
        self.key_mappings = {
            "builds": {
                "hash": "hash",
                "type": "type",
                "pull_request": "pr_number",
                "label": "label_name",
                "created_at": "creation_date",
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
            "pr_mapping_data": {
                "html_url" : "pr_url",
                "number": "pr_number",
                "title": "pr_title",
                "user.login": "pr_user"
            },
        }

    def get_nested_value(self, data, nested_key):
        """Retrieve the nested value from a dictionary using dotted key notation."""
        keys = nested_key.split(".")
        temp_data = data
        for key in keys:
            try:
                temp_data = temp_data[key]
            except KeyError:
                return None
        return temp_data


    def combine_data(self, builds, testruns, pr_mapping_data):
        combined_data = {}

        for build in builds:
            self.process_build(build, combined_data)

        for testrun in testruns:
            self.process_testrun(testrun, combined_data)

        for hash_value, pr_data in pr_mapping_data.items():
            self.process_pr_mapping_data(hash_value, pr_data, combined_data)

        self.compute_all_stats(combined_data)

        # with open('./combined_data.json', 'w') as file:
        #     json.dump(combined_data, file, indent=4)

        return list(combined_data.values())
        # return combined_data



    def process_build(self, build, combined_data):
        mapped_build = self._map_keys(build, "builds")
        hash_value = mapped_build.get("hash")
        build_status = mapped_build.get('build_status')

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
        combined_data.setdefault(hash_value, {}).update(mapped_testrun)

    def process_pr_mapping_data(self, hash_value, pr_data, combined_data):
        mapped_pr_data = self._map_keys(pr_data, "pr_mapping_data")
        self._add_custom_fields(mapped_pr_data)
        combined_data.setdefault(hash_value, {}).update(mapped_pr_data)


    def _add_custom_fields(self, pr_data):
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
            test_status = 'PASS' if fail_count == 0 else 'FAIL'

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



