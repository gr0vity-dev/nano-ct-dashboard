import statistics
from datetime import datetime
from collections import defaultdict
from typing import List, Optional

from app.services.github_helper import GithubUrlBuilder
from app.services.helper_service import DateTimeHelper
import warnings



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
                "built_at": "build_date",
                "build_status": "build_status",
                "docker_tag": "docker_tag",
            },
            "testruns": {
                "hash": "hash",
                "type": "type",
                "pull_request": "pr_number",
                "started_at": "start_date",
                "completed_at": "completion_date",
                "testcases": "testcases",
                "overall_status": "overall_test_status"
            },
            "pr_mapping_data": {
                "html_url" : "pr_url",
                "number": "pr_number",
                "title": "pr_title",

            },
        }



    def combine_data(self, builds, testruns, pr_mapping_data):
        combined_data = {}

        for build in builds:
            self.process_build(build, combined_data)

        for testrun in testruns:
            self.process_testrun(testrun, combined_data)

        for hash_value, pr_data in pr_mapping_data.items():
            self.process_pr_mapping_data(hash_value, pr_data, combined_data)

        self.remove_unwanted_data(combined_data)

        return combined_data

    def process_build(self, build, combined_data):
        mapped_build = self._map_keys(build, "builds")
        hash_value = mapped_build.get("hash")

        if not hash_value:
            warnings.warn("Encountered data without a hash!")
            return

        combined_data[hash_value] = mapped_build


    def process_testrun(self, testrun, combined_data):
        hash_value = testrun.get("hash")
        if not hash_value:
            return

        if hash_value not in combined_data:
            combined_data[hash_value] = {}

        for input_key, output_key in self.key_mappings["testruns"].items():
            if input_key in testrun:
                combined_data[hash_value][output_key] = testrun[input_key]
            else :
                warnings.warn(f"Missing input key {input_key}")

    def process_pr_mapping_data(self, hash_value, pr_data, combined_data):
        if hash_value not in combined_data:
            combined_data[hash_value] = {}

        for input_key, output_key in self.key_mappings["pr_mapping_data"].items():
            if input_key in pr_data:
                combined_data[hash_value][output_key] = pr_data[input_key]
            else:
                # Issue a warning if an expected key is missing
                warnings.warn(f"Missing input key {input_key} in pr_mapping_data for hash {hash_value}", UserWarning)


    def remove_unwanted_data(self, combined_data):
        for key, value in list(combined_data.items()):  # Using list() to make a copy for iteration.
            if value.get('build_status') not in ['pass', 'fail', 'building']:
                warnings.warn(f"Encountered {value.get('build_status')} data for hash: {key}", UserWarning)
                del combined_data[key]



    def _map_keys(self, data, data_type):
        mapped_data = {}
        for input_key, output_key in self.key_mappings[data_type].items():
            if input_key in data:  # Check if the input key exists in the data
                mapped_data[output_key] = data[input_key]
        return mapped_data