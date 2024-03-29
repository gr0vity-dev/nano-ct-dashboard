from datetime import datetime
from collections import defaultdict
import statistics


class DateTimeHelper:

    @staticmethod
    def get_duration_in_s(started_at, completed_at) -> str:
        if not started_at or not completed_at:
            return None
        duration = None
        if started_at and completed_at:
            duration = int((datetime.fromisoformat(completed_at.rstrip('Z'))
                            - datetime.fromisoformat(
                started_at.rstrip('Z'))).total_seconds())
        return duration

    @staticmethod
    def compute_test_duration(started_at, completed_at) -> str:
        return DateTimeHelper.get_duration_in_s(started_at, completed_at)

    @staticmethod
    def compute_time_elapsed(test_started_at):
        if not test_started_at:
            return None
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
    def compute_median_commit_durations(combined_data, commit_count=10):
        # Dictionary to hold durations of each testcase with their completion dates
        testcase_info = defaultdict(list)

        # Loop through each entry in data to gather durations and completion dates for each testcase
        for entry in combined_data:
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
            sorted_info = sorted(info, key=lambda x: x["completed_at"], reverse=True)[
                :commit_count]
            durations = [item["duration"] for item in sorted_info]
            median_durations[testcase] = statistics.median(durations)

        return median_durations

    @staticmethod
    def compute_median_stats(testcase, median_durations):
        # Compute basic stats
        median_duration = median_durations.get(testcase["testcase"], None)
        if not median_duration:
            return testcase

        duration = testcase["duration"]
        deviation_from_median = duration - median_duration
        deviation_from_median_percent = (
            deviation_from_median / median_duration) * 100

        # Update the testcase with computed values
        testcase.update({
            "commit_median_duration": median_duration,
            "deviation_from_median": deviation_from_median,
            "deviation_from_median_percent": round(deviation_from_median_percent, 1)
        })

        # Check against threshold and update status if necessary
        excess_threshold_percent = 25
        testcase["excess_threshold_percent"] = excess_threshold_percent
        threshold_duration = (
            1 + (excess_threshold_percent / 100)) * median_duration

        if testcase["status"] == "PASS" and duration > threshold_duration:
            testcase["status"] = "WARN"

        return testcase

    @staticmethod
    def assign_revisions(combined_data):
        pr_groups = defaultdict(list)
        max_revisions = {}
        first_pr_timestamps = {}
        sorted_entries = sorted(combined_data, key=lambda x: x.get(
            'built_at', x.get('created_at', '1970-01-01T00:00:00Z')), reverse=False)

        # Group entries by pr_number and compute max revisions for each PR
        for entry in sorted_entries:
            if entry.get("type") == "pull_request":
                # Convert to integer for consistency
                pr_number = entry["pr_number"]
                pr_groups[pr_number].append(entry)
                # Sort and assign revision for PRs
                sorted_pr_entries = sorted(
                    pr_groups[pr_number], key=lambda x: x.get("built_at", ""))
                for i, pr_entry in enumerate(sorted_pr_entries):
                    pr_entry["revision_number"] = i + 1
                    if i == 0 and "built_at" in pr_entry:  # This is the first PR for this PR number
                        first_pr_timestamps[pr_number] = pr_entry["built_at"]
                max_revisions[pr_number] = len(sorted_pr_entries)

            elif entry.get("type") == "commit":
                pr_number = entry.get("pr_number")
                if pr_number is None or pr_number not in first_pr_timestamps:
                    # If no PR number exists, indicate 'direct'
                    entry["pr_number"] = "N/A"
                    entry["revision_number"] = "0"
                    entry["duration_from_first_pr_to_commit"] = "direct"
                else:
                    entry["revision_number"] = max_revisions.get(pr_number, 1)
                    if "built_at" in entry:
                        commit_datetime = datetime.fromisoformat(
                            entry["built_at"].rstrip("Z"))
                        first_pr_datetime = datetime.fromisoformat(
                            first_pr_timestamps[pr_number].rstrip("Z"))
                        duration = commit_datetime - first_pr_datetime
                        entry["duration_from_first_pr_to_commit"] = str(
                            duration.days) + " day(s)" if duration.days != 0 else "<1 day"
