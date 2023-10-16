import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from datetime import datetime, timedelta
from app.services.report_combiner import DataCombiner
from app.services.helper_service import DateTimeHelper, TestCaseHelper
from app.services.data_processor import BuildProcessor, PRInfoProcessor, TestrunProcessor




def read_test_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def test_combined_build_status():
    test_files = {
        'unit_tests/data/build_pass.json': 'pass',
        'unit_tests/data/build_running.json': 'building',
        'unit_tests/data/build_fail.json': 'fail',
    }

    for filename, expected_status in test_files.items():
        test_data = read_test_data(filename)
        processors = [BuildProcessor("", test_data)]
        combined_data = DataCombiner(processors).combine_data_as_dict()

        for item in test_data:
            assert item['hash'] in combined_data
            assert expected_status == combined_data[item['hash']]['build_status']

def test_warning_for_special_cases():
    special_files = [
        'unit_tests/data/build_empty.json',
        'unit_tests/data/build_trash.json',
    ]

    for filename in special_files:
        with pytest.warns(UserWarning):  # Expecting a UserWarning for the special cases.
            test_data = read_test_data(filename)
            processors = [BuildProcessor("", test_data)]
            combined_data = DataCombiner(processors).combine_data_as_dict()


def test_no_fail_for_missing_keys():
    test_data = read_test_data('unit_tests/data/builds.json')
    # Add a build with a missing key
    faulty_build = {
        "wrong_key": "value",
        "hash": "nonexistent_hash"
    }
    test_data.append(faulty_build)

    # Check that it doesn't raise an exception
    try:
        with pytest.warns(UserWarning):  # Expecting a UserWarning when no hash exists
            processors = [BuildProcessor("", test_data)]
            combined_data = DataCombiner(processors).combine_data_as_dict()
            assert "nonexistent_hash" not in combined_data  # It should not add the faulty build to the output
    except Exception as e:
        pytest.fail(f"Function should not fail for missing keys, but got exception: {e}")


def test_proper_combination_of_build_and_testrun():
    build_data = read_test_data('unit_tests/data/builds.json')
    testrun_data = read_test_data('unit_tests/data/testruns.json')
    processors = [BuildProcessor("", build_data), TestrunProcessor(testrun_data)]
    combined_data = DataCombiner(processors).combine_data_as_dict()

    # Here we just test a sample key combination to ensure data from both sources are combined
    for build in build_data:
        assert build["hash"] in combined_data
        assert combined_data[build["hash"]]["created_at"] == build["created_at"]

    for testrun in testrun_data:
        assert testrun["hash"] in combined_data
        assert combined_data[testrun["hash"]]["test_started_at"] == testrun["started_at"]


def test_ignoring_unmapped_keys():
    build_data = read_test_data('unit_tests/data/builds.json')
    testrun_data = read_test_data('unit_tests/data/testruns.json')
    for tr in testrun_data:
        tr["unmapped_key"] = "some_value"

    processors = [BuildProcessor("", build_data), TestrunProcessor(testrun_data)]
    combined_data = DataCombiner(processors).combine_data_as_dict()

    for tr in testrun_data:
        hash_value = tr.get("hash")
        assert "unmapped_key" not in combined_data[hash_value]


def test_proper_combination_of_all_data():
    build_data = read_test_data('unit_tests/data/builds.json')
    testrun_data = read_test_data('unit_tests/data/testruns.json')
    pr_info = read_test_data('unit_tests/data/pr_info.json')

    processors = [BuildProcessor("", build_data), TestrunProcessor(testrun_data), PRInfoProcessor(pr_info)]
    combined_data = DataCombiner(processors).combine_data_as_dict()

    for hash_value, pr_data in pr_info.items():
        assert hash_value in combined_data
        assert combined_data[hash_value]["pr_url"] == pr_data["html_url"]


def test_ignoring_unmapped_keys_in_pr_info():
    build_data = read_test_data('unit_tests/data/builds.json')
    testrun_data = read_test_data('unit_tests/data/testruns.json')
    pr_info = read_test_data('unit_tests/data/pr_info.json')
    for hash_value, pr_data in pr_info.items():
        pr_data["unmapped_key"] = "some_value"

    processors = [BuildProcessor("", build_data), TestrunProcessor(testrun_data), PRInfoProcessor(pr_info)]
    combined_data = DataCombiner(processors).combine_data_as_dict()

    for hash_value in pr_info:
        assert "unmapped_key" not in combined_data[hash_value]


def test_nested_key_mapping_for_pr_info():
    build_data = read_test_data('unit_tests/data/builds.json')
    pr_info = read_test_data('unit_tests/data/pr_info.json')

    processors = [BuildProcessor("", build_data), PRInfoProcessor(pr_info)]
    combined_data = DataCombiner(processors).combine_data_as_dict()

    for hash_value, pr in pr_info.items():
        assert pr["user"]["login"] == combined_data[hash_value]["pr_user"]



def test_testduration_calculation():

    test_started_at =  "2023-09-26T08:51:08Z"
    test_completed_at = "2023-09-26T08:54:22Z"
    test_duration = DateTimeHelper.compute_test_duration(test_started_at,test_completed_at)
    assert test_duration == 194  # 08:54:22 - 08:51:08 in seconds


def test_testage_calculation():
    # Get current time and subtract 240 seconds (4 minutes) to get the start time
    sample_time = 238
    sample_test_started_at = (datetime.utcnow() - timedelta(seconds=sample_time)).strftime("%Y-%m-%dT%H:%M:%SZ")
    test_age = DateTimeHelper.compute_time_elapsed(sample_test_started_at)
    assert test_age == "3 minute(s)"  # 4 minutes in se

    sample_time = 240
    sample_test_started_at = (datetime.utcnow() - timedelta(seconds=sample_time)).strftime("%Y-%m-%dT%H:%M:%SZ")
    test_age = DateTimeHelper.compute_time_elapsed(sample_test_started_at)
    assert test_age == "4 minute(s)"  # 4 minutes in se

    sample_time = 3600
    sample_test_started_at = (datetime.utcnow() - timedelta(seconds=sample_time)).strftime("%Y-%m-%dT%H:%M:%SZ")
    test_age = DateTimeHelper.compute_time_elapsed(sample_test_started_at)
    assert test_age == "1 hour(s)"  # 4 minutes in se

    sample_time = 4 * 24 *3600
    sample_test_started_at = (datetime.utcnow() - timedelta(seconds=sample_time)).strftime("%Y-%m-%dT%H:%M:%SZ")
    test_age = DateTimeHelper.compute_time_elapsed(sample_test_started_at)
    assert test_age == "4 day(s)"  # 4 minutes in se


def test_commit_median_duration_calculation():
    sample_data = [
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 1 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 1 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 1 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 1 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 1 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 100 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 100 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 100 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 100 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-26T08:53:28Z","duration": 100 } ] },
        {"type": "commit","testcases": [{"testcase": "5n4pr_conf_10k_bintree","completed_at": "2023-09-28T00:00:00","duration": 5 } ] }
    ]
    median_durations = TestCaseHelper.compute_median_commit_durations(sample_data)
    # Assuming median duration based on your sample data
    assert median_durations == {"5n4pr_conf_10k_bintree" : 3}


def test_testcases_stats_calculation():
    sample_testcase = {
        "testcase": "5n4pr_conf_10k_bintree",
        "started_at": "2023-09-20T17:04:01Z",
        "completed_at": "2023-09-20T17:05:49Z",
        "duration": 108,
        "status" : "PASS"
    }
    # Assuming a set median value for this example
    median_value = {"5n4pr_conf_10k_bintree" : 85.5, "X" : 33}
    updated_testcase = TestCaseHelper.compute_median_stats(sample_testcase, median_value)

    assert updated_testcase["deviation_from_median"] == 22.5
    assert updated_testcase["deviation_from_median_percent"] == 26.3
    assert updated_testcase["excess_threshold_percent"] == 25
    assert updated_testcase["status"] == "WARN"

def test_assign_revisions():
    # Sample data
    combined_data = [
        {"hash": "hash4","type": "commit","pr_number": "123","built_at": "2023-09-28T22:11:53Z"},
        {"hash": "hash1","type": "pull_request","pr_number": "123","built_at": "2023-09-25T22:11:53Z"},
        {"hash": "hash2","type": "pull_request","pr_number": "123","built_at": "2023-09-26T22:11:53Z"},
        {"hash": "hash3","type": "pull_request","pr_number": "123","built_at": "2023-09-27T22:11:53Z"},
        {"hash": "hash5","type": "commit","pr_number": "123","built_at": "2023-09-29T22:11:53Z"}
    ]

    TestCaseHelper.assign_revisions(combined_data)

    # Asserting revisions are assigned as expected
    assert combined_data[1]["revision_number"] == 1
    assert combined_data[2]["revision_number"] == 2
    assert combined_data[3]["revision_number"] == 3
    assert combined_data[4]["revision_number"] == 3
    assert combined_data[0]["revision_number"] == 3
