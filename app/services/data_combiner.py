import statistics
from datetime import datetime
from collections import defaultdict
from typing import List, Optional

from app.services.github_helper import GithubUrlBuilder
from app.services.helper_service import DateTimeHelper


def get_timestamp(entry):
    return datetime.strptime(entry["created_at"], "%Y-%m-%dT%H:%M:%SZ")


def handle_pull_request(entry, pr_revisions, first_pr_timestamps):
    pr_number = entry.get("pull_request")
    if pr_number is None:
        return

    pr_revisions[pr_number] += 1
    if pr_number not in first_pr_timestamps:
        first_pr_timestamps[pr_number] = get_timestamp(entry)

    entry["revision_number"] = pr_revisions[pr_number]


def handle_commit(entry, pr_revisions, first_pr_timestamps):
    pr_number = entry.get("pull_request", None)
    entry["revision_number"] = pr_revisions.get(pr_number, 1)

    if pr_number in first_pr_timestamps:
        commit_timestamp = get_timestamp(entry)
        duration = commit_timestamp - first_pr_timestamps[pr_number]
        entry["duration_from_first_pr_to_commit"] = str(
            duration.days) if duration.days != 0 else "<1"
    else:
        entry["duration_from_first_pr_to_commit"] = None


class DataCombiner:

    def __init__(self, url_builder: GithubUrlBuilder,
                 datetime_helper: DateTimeHelper):
        self.url_builder = url_builder
        self.datetime_helper = datetime_helper

    def compute_time_elapsed(self, test_started_at):
        time_elapsed = ""
        test_started_at = datetime.strptime(test_started_at,
                                            "%Y-%m-%dT%H:%M:%SZ")
        time_elapsed = datetime.utcnow() - test_started_at

        if time_elapsed.total_seconds(
        ) >= 3600:  # More than or equal to 1 hour
            if time_elapsed.total_seconds(
            ) >= 86400:  # More than or equal to 24 hours
                days_elapsed = time_elapsed.days
                time_elapsed = f"{days_elapsed} days"
            else:
                hours_elapsed = time_elapsed.total_seconds() // 3600
                time_elapsed = f"{hours_elapsed} hours"
        else:
            minutes_elapsed = time_elapsed.total_seconds() // 60
            time_elapsed = f"{minutes_elapsed} minutes"
        return time_elapsed

    # Define the filtering rules
    def filter_rules(self, item):
        build_status = item.get("build_status")
        created_at_str = item.get("created_at")
        test_count = item.get("test_count") or 0
        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.utcnow()
        time_diff = now - created_at

        return build_status and ((build_status == "building"
                                  and time_diff.total_seconds() <= 3 * 60 * 60)
                                 or build_status == "pass") and test_count > 0

    def update_builds_dict(self, testrun, builds_dict):
        test_hash = testrun.get('hash')
        if test_hash not in builds_dict:
            return

        testcases = testrun.get('testcases', [])
        for testcase in testcases:
            testcase["duration"] = self.datetime_helper.get_duration_in_s(
                testcase.get("started_at"), testcase.get("completed_at"))
            if testcase.get("status") == "FAIL":
                testcase["report_url"] = self.url_builder.get_report_url(
                    test_hash, testcase["testcase"])
                builds_dict[test_hash][
                    "github_url"] = self.url_builder.create_gh_url(
                        builds_dict[test_hash])
        testcases.sort(key=lambda x: x['testcase'])

        overall_started_at = testrun.get('started_at')
        overall_completed_at = testrun.get('completed_at')
        overall_status = testrun.get('overall_status')
        pr_number = testrun.get('pull_request')

        builds_dict[test_hash]['pull_request'] = str(
            pr_number or builds_dict[test_hash].get('pull_request', ""))
        builds_dict[test_hash]['test_status'] = overall_status
        builds_dict[test_hash]['test_started_at'] = overall_started_at
        builds_dict[test_hash]['test_age'] = self.compute_time_elapsed(
            overall_started_at)
        builds_dict[test_hash]['test_completed_at'] = overall_completed_at
        builds_dict[test_hash]['test_count'] = len(testcases)
        builds_dict[test_hash]['fail_count'] = len([
            testcase for testcase in testcases if testcase['status'] == 'FAIL'
        ])
        builds_dict[test_hash]['pass_count'] = len([
            testcase for testcase in testcases if testcase['status'] == 'PASS'
        ])
        builds_dict[test_hash][
            'test_duration'] = self.datetime_helper.get_duration_in_s(
                overall_started_at, overall_completed_at)
        builds_dict[test_hash]['hash_url'] = self.url_builder.create_gh_url(
            builds_dict[test_hash])
        builds_dict[test_hash]['testcases'] = testcases

    def compute_median_duration(self, list_entries: list):
        testcase_durations = {}
        median_on_count = 100

        for counter, entry in enumerate(list_entries):
            #compute median duration for committed testcases only
            if "testcases" not in entry: continue
            if entry["type"] != "commit": continue

            for testcase in entry["testcases"]:
                testcase_name = testcase["testcase"]
                testcase_duration = int(testcase["duration"])
                testcase_durations.setdefault(testcase_name,
                                              []).append(testcase_duration)
            #only calculate the median on a subset of the last {median_on_count} elements
            if counter > median_on_count: break

        for entry in list_entries:
            for testcase in entry["testcases"]:
                testcase_name = testcase["testcase"]
                duration = testcase["duration"]
                median_duration = statistics.median(
                    testcase_durations[testcase_name])
                testcase["commit_median_duration"] = median_duration
                testcase["deviation_from_median"] = duration - median_duration
                testcase["deviation_from_median_percent"] = float(
                    "{:.1f}".format(
                        ((duration - median_duration) / median_duration) *
                        100))

                #set status of testcase to warning if duration exceeds excess_threshold_percent
                excess_threshold_percent = 25
                testcase["excess_threshold_percent"] = excess_threshold_percent
                if testcase["duration"] > (
                        1 +
                    (excess_threshold_percent / 100)) * median_duration:
                    testcase["status"] = "WARN"

        return list_entries

    def extend_data(self, data: List[dict]):
        pull_request_revisions = defaultdict(int)
        first_pull_request_timestamps = {}

        data = sorted(data, key=get_timestamp)

        for entry in data:
            if entry["type"] == "pull_request":
                handle_pull_request(entry, pull_request_revisions,
                                    first_pull_request_timestamps)
            elif entry["type"] == "commit":
                handle_commit(entry, pull_request_revisions,
                              first_pull_request_timestamps)

        return data

    async def combine_data(self, builds, testruns):
        builds_dict = {build['hash']: build for build in builds}

        for testrun in testruns:
            self.update_builds_dict(testrun, builds_dict)

        combined_data = list(builds_dict.values())
        combined_data = [
            item for item in combined_data if self.filter_rules(item)
        ]

        self.extend_data(combined_data)
        self.compute_median_duration(combined_data)

        combined_data.sort(key=lambda x: x['built_at'], reverse=True)

        #compute median execution time per test and the deviation of teh current test from median duration

        return combined_data
