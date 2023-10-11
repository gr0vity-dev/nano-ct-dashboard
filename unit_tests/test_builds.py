import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from app.services.report_combiner import DataCombiner

import json
import pytest
from app.services.report_combiner import DataCombiner

def read_test_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def test_iteration_over_builds():
    test_data = read_test_data('unit_tests/data/builds.json')
    combined_data = DataCombiner().combine_data(test_data, [], {})

    for item in test_data:
        assert item['hash'] in combined_data
        assert item['build_status'] == combined_data[item['hash']]['build_status']

def test_combined_build_status():
    test_files = {
        'unit_tests/data/build_pass.json': 'pass',
        'unit_tests/data/build_running.json': 'building',
        'unit_tests/data/build_fail.json': 'fail',
    }

    for filename, expected_status in test_files.items():
        test_data = read_test_data(filename)
        combined_data = DataCombiner().combine_data(test_data, [], {})

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
            combined_data = DataCombiner().combine_data(test_data, [], {})


def test_key_mapping():
    test_data = read_test_data('unit_tests/data/builds.json')
    combiner = DataCombiner()
    combined_data = combiner.combine_data(test_data, [], {})

    for build in test_data:
        hash_value = build.get("hash")
        mapped_build = combined_data[hash_value]

        # Check all input keys are mapped correctly
        for input_key, output_key in combiner.key_mappings["builds"].items():
            if input_key in build:
                assert build[input_key] == mapped_build[output_key]

def test_no_fail_for_missing_keys():
    test_data = read_test_data('unit_tests/data/builds.json')
    combiner = DataCombiner()
    # Add a build with a missing key
    faulty_build = {
        "wrong_key": "value",
        "hash": "nonexistent_hash"
    }
    test_data.append(faulty_build)

    # Check that it doesn't raise an exception
    try:
        with pytest.warns(UserWarning):  # Expecting a UserWarning when no hash exists
            combined_data = combiner.combine_data(test_data, [], {})
            assert "nonexistent_hash" not in combined_data  # It should not add the faulty build to the output
    except Exception as e:
        pytest.fail(f"Function should not fail for missing keys, but got exception: {e}")

def test_key_mapping_for_testruns():
    build_data = read_test_data('unit_tests/data/builds.json')
    test_data = read_test_data('unit_tests/data/testruns.json')
    combiner = DataCombiner()
    combined_data = combiner.combine_data(build_data, test_data, {})

    for testrun in test_data:
        hash_value = testrun.get("hash")
        mapped_testrun = combined_data[hash_value]

        for input_key, output_key in combiner.key_mappings["testruns"].items():
            assert testrun[input_key] == mapped_testrun[output_key]

def test_warning_for_missing_input_key():
    faulty_testrun = {
        "hash": "some_hash",
        "wrong_key": "value",
    }
    combiner = DataCombiner()

    with pytest.warns(UserWarning, match="Missing input key"):
        combiner.combine_data([], [faulty_testrun], {})

def test_proper_combination_of_build_and_testrun():
    build_data = read_test_data('unit_tests/data/builds.json')
    testrun_data = read_test_data('unit_tests/data/testruns.json')
    combiner = DataCombiner()
    combined_data = combiner.combine_data(build_data, testrun_data, {})

    # Here we just test a sample key combination to ensure data from both sources are combined
    for build in build_data:
        assert build["hash"] in combined_data
        assert combined_data[build["hash"]]["creation_date"] == build["created_at"]

    for testrun in testrun_data:
        assert testrun["hash"] in combined_data
        assert combined_data[testrun["hash"]]["start_date"] == testrun["started_at"]


def test_ignoring_unmapped_keys():
    build_data = read_test_data('unit_tests/data/builds.json')
    test_data = read_test_data('unit_tests/data/testruns.json')
    for tr in test_data:
        tr["unmapped_key"] = "some_value"
    combiner = DataCombiner()
    combined_data = combiner.combine_data(build_data, test_data, {})

    for tr in test_data:
        hash_value = tr.get("hash")
        assert "unmapped_key" not in combined_data[hash_value]


def test_key_mapping_for_pr_mapping_data():
    build_data = read_test_data('unit_tests/data/builds.json')
    test_data = read_test_data('unit_tests/data/testruns.json')
    pr_mapping_data = read_test_data('unit_tests/data/mappings.json')
    combiner = DataCombiner()
    combined_data = combiner.combine_data(build_data, test_data, pr_mapping_data)

    for hash_value, pr_data in pr_mapping_data.items():
        mapped_pr_data = combined_data[hash_value]

        for input_key, output_key in combiner.key_mappings["pr_mapping_data"].items():
            assert pr_data[input_key] == mapped_pr_data[output_key]


def test_warning_for_missing_input_key_in_pr_mapping_data():
    build_data = [{
        "hash": "some_hash"
    }]

    faulty_pr_data = {
        "hash": "some_hash",
        "wrong_key": "value",
    }
    combiner = DataCombiner()

    with pytest.warns(UserWarning, match="Missing input key"):
        combiner.combine_data(build_data, [], {faulty_pr_data["hash"]: faulty_pr_data})


def test_proper_combination_of_all_data():
    build_data = read_test_data('unit_tests/data/builds.json')
    testrun_data = read_test_data('unit_tests/data/testruns.json')
    pr_mapping_data = read_test_data('unit_tests/data/mappings.json')
    combiner = DataCombiner()
    combined_data = combiner.combine_data(build_data, testrun_data, pr_mapping_data)

    for hash_value, pr_data in pr_mapping_data.items():
        assert hash_value in combined_data
        assert combined_data[hash_value]["pr_url"] == pr_data["html_url"]


def test_ignoring_unmapped_keys_in_pr_mapping_data():
    build_data = read_test_data('unit_tests/data/builds.json')
    test_data = read_test_data('unit_tests/data/testruns.json')
    pr_mapping_data = read_test_data('unit_tests/data/mappings.json')
    for hash_value, pr_data in pr_mapping_data.items():
        pr_data["unmapped_key"] = "some_value"
    combiner = DataCombiner()
    combined_data = combiner.combine_data(build_data, test_data, pr_mapping_data)

    for hash_value in pr_mapping_data:
        assert "unmapped_key" not in combined_data[hash_value]
