from datetime import datetime
from collections import defaultdict
import statistics



class DateTimeHelper:

    @staticmethod
    def get_duration_in_s(started_at, completed_at) -> str:
        duration = None
        if started_at and completed_at:
            duration = int((datetime.fromisoformat(completed_at.rstrip('Z'))
                     - datetime.fromisoformat(
                         started_at.rstrip('Z'))).total_seconds())
        return duration

    @staticmethod
    def compute_test_duration(started_at, completed_at) -> str:
        return  DateTimeHelper.get_duration_in_s(started_at, completed_at)

    @staticmethod
    def compute_time_elapsed(test_started_at):
        time_elapsed = ""
        test_started_at = datetime.strptime(test_started_at,
                                            "%Y-%m-%dT%H:%M:%SZ")
        time_elapsed = datetime.utcnow() - test_started_at

        if time_elapsed.total_seconds(
        ) >= 3600:  # More than or equal to 1 hour
            if time_elapsed.total_seconds(
            ) >= 86400:  # More than or equal to 24 hours
                days_elapsed = time_elapsed.days
                time_elapsed = f"{int(days_elapsed)} day(s)"
            else:
                hours_elapsed = time_elapsed.total_seconds() // 3600
                time_elapsed = f"{int(hours_elapsed)} hour(s)"
        else:
            minutes_elapsed = time_elapsed.total_seconds() // 60
            time_elapsed = f"{int(minutes_elapsed)} minute(s)"
        return time_elapsed


class TestCaseHelper:

    @staticmethod
    def compute_commit_median_durations(combined_data):
        # Dictionary to hold durations of each testcase with their completion dates
        testcase_info = defaultdict(list)

        # Loop through each entry in data to gather durations and completion dates for each testcase
        for entry in combined_data.values():
            if entry.get("type") == "commit":
                for testcase in entry.get("testcases", []):
                    if "duration" in testcase and "completed_at" in testcase:
                        testcase_name = testcase["testcase"]
                        testcase_info[testcase_name].append({
                            "duration": testcase["duration"],
                            "completed_at": datetime.fromisoformat(testcase["completed_at"].rstrip("Z"))
                        })

        # Now, sort by completion date, take the 10 most recent testcases and compute the median for each testcase
        median_durations = {}
        for testcase, info in testcase_info.items():
            sorted_info = sorted(info, key=lambda x: x["completed_at"], reverse=True)[:10]  # 10 most recent
            durations = [item["duration"] for item in sorted_info]
            median_durations[testcase] = statistics.median(durations)

        return median_durations


    @staticmethod
    def compute_single_testcase_stats(testcase, median_durations):
        # Compute basic stats
        median_duration = median_durations[testcase["testcase"]]
        duration = testcase["duration"]
        deviation_from_median = duration - median_duration
        deviation_from_median_percent = (deviation_from_median / median_duration) * 100

        # Update the testcase with computed values
        testcase.update({
            "commit_median_duration": median_duration,
            "deviation_from_median": deviation_from_median,
            "deviation_from_median_percent": round(deviation_from_median_percent, 1)
        })

        # Check against threshold and update status if necessary
        excess_threshold_percent = 25
        testcase["excess_threshold_percent"] = excess_threshold_percent
        threshold_duration = (1 + (excess_threshold_percent / 100)) * median_duration

        if testcase["status"] == "PASS" and duration > threshold_duration:
            testcase["status"] = "WARN"

        return testcase

    # @staticmethod
    # def assign_revisions(combined_data):
    #     pr_groups = defaultdict(list)
    #     max_revisions = {}

    #     # Group entries by pr_number and compute max revisions for each PR
    #     for _, entry in combined_data.items():
    #         if entry.get("type") == "pull_request":
    #             pr_number = int(entry["pr_number"])  # Convert to integer for consistency
    #             pr_groups[pr_number].append(entry)
    #             # Sort and assign revision for PRs
    #             sorted_entries = sorted(pr_groups[pr_number], key=lambda x: x["build_date"])
    #             for i, pr_entry in enumerate(sorted_entries):
    #                 pr_entry["revision"] = i + 1
    #             max_revisions[pr_number] = len(sorted_entries)
    #         elif entry["type"] == "commit" and int(entry.get("pr_number", 0)) in max_revisions:
    #             entry["revision"] = max_revisions[int(entry["pr_number"])]

    @staticmethod
    def assign_revisions(combined_data):
        pr_groups = defaultdict(list)
        max_revisions = {}

        # Group entries by pr_number and compute max revisions for each PR
        for entry in combined_data.values():
            if entry.get("type") == "pull_request":
                pr_number = int(entry["pr_number"])  # Convert to integer for consistency
                pr_groups[pr_number].append(entry)
                # Sort and assign revision for PRs
                sorted_entries = sorted(pr_groups[pr_number], key=lambda x: x["built_at"])
                for i, pr_entry in enumerate(sorted_entries):
                    pr_entry["revision"] = i + 1
                max_revisions[pr_number] = len(sorted_entries)
            elif entry.get("type") == "commit" and int(entry.get("pr_number", 0)) in max_revisions:
                entry["revision"] = max_revisions[int(entry["pr_number"])]




