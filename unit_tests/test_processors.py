import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from app.services.data_processor import BuildProcessor, TestrunProcessor, PRInfoProcessor
from app.services.report_combiner import DataCombiner



def read_test_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def test_build_processor():
    test_files = ['unit_tests/data/build_pass.json' ]

    for filename in test_files:
        test_data = read_test_data(filename)
        repo_url = "github.com/x/y"
        processor = BuildProcessor(repo_url)
        processor.process(test_data[0])
        processed_data = processor.get_processed_data()

        hash = test_data[0]["hash"]
        assert len(processed_data[hash].values()) > 1

        assert processed_data[hash]['hash'] == '001549ab5455f32f7d887814b30b50b3c668bc63'
        assert processed_data[hash]['type'] == 'pull_request'
        assert processed_data[hash]['pr_number'] == 4295
        assert processed_data[hash]['label'] == 'clemahieu:block_split'
        assert processed_data[hash]['created_at'] == '2023-09-25T22:11:53Z'
        assert processed_data[hash]['built_at'] == '2023-09-25T23:07:54Z'
        assert processed_data[hash]['build_status'] == 'pass'
        assert processed_data[hash]['docker_tag'] == 'gr0v1ty/nano-node:001549ab5455f32f7d887814b30b50b3c668bc63'
        assert processed_data[hash]['hash_url'] == 'github.com/x/y/commit/001549ab5455f32f7d887814b30b50b3c668bc63'


def test_pr_info_processor():
    test_files = ['unit_tests/data/pr_info.json']

    for filename in test_files:
        test_data = read_test_data(filename)
        hash, value = next(iter(test_data.items()))
        processor = PRInfoProcessor()  # Assuming you have a different processor for each data type
        processor.process((hash, value))
        processed_data = processor.get_processed_data()


        assert len(processed_data[hash]) > 1
        # Assuming test_data[0] contains the same keys you've provided in key_mappings
        assert processed_data[hash]['pr_url'] == 'https://github.com/nanocurrency/nano-node/pull/4287'
        assert processed_data[hash]['pr_number'] == 4287
        assert processed_data[hash]['pr_title'] == 'Nano store cleanup'
        assert processed_data[hash]['pr_user'] == 'clemahieu'
        assert processed_data[hash]['diff_url'] == 'https://github.com/nanocurrency/nano-node/pull/4287/files?diff=split&w=0'



def test_testruns_processor():
    test_files = ['unit_tests/data/testruns.json']

    for filename in test_files:
        test_data = read_test_data(filename)
        processor = TestrunProcessor()  # Assuming you have a different processor for each data type
        processor.process(test_data[0])
        processed_data = processor.get_processed_data()

        print(processed_data)

        hash = test_data[0]["hash"]
        assert len(processed_data[hash].values()) > 1

        # Assuming test_data[0] contains the same keys you've provided in key_mappings
        assert processed_data[hash]['hash'] == '001549ab5455f32f7d887814b30b50b3c668bc63'
        assert processed_data[hash]['type'] == 'pull_request'
        assert processed_data[hash]['pr_number'] == 4295
        assert processed_data[hash]['test_started_at'] == '2023-09-26T08:51:08Z'
        assert processed_data[hash]['test_completed_at'] == '2023-09-26T08:54:22Z'
        assert len(processed_data[hash]['testcases']) == 5
        assert processed_data[hash]['overall_status'] == 'FAIL'
        assert processed_data[hash]['test_duration'] == 194
        assert "test_age" in processed_data[hash]
        assert processed_data[hash]["test_status"] ==  "FAIL"
        assert processed_data[hash]["test_count"] ==  5
        assert processed_data[hash]["fail_count"] ==  4
        assert processed_data[hash]["pass_count"] ==  1

        for testcase in processed_data[hash]['testcases']:
            assert "duration" in testcase
            assert testcase["duration"] > 0


def test_builds_key_mapping():
    test_data = read_test_data('unit_tests/data/builds.json')
    repo_url = "github.com/x/y"
    processor = BuildProcessor(repo_url)

    for build in test_data:
        processor.process(build)
        processed_data = processor.get_processed_data()
        hash_value = build.get("hash")
        mapped_build = processed_data[hash_value]

        assert len(mapped_build) > 1

        # Check all input keys are mapped correctly
        for input_key, output_key in processor.key_mappings.items():
            if input_key in build:
                assert build[input_key] == mapped_build[output_key]



def test_testruns_key_mapping():
    test_data = read_test_data('unit_tests/data/testruns.json')
    processor = TestrunProcessor()  # Assuming you have a different processor for each data type
    for testrun in test_data:
        processor.process(testrun)
        processed_data = processor.get_processed_data()

        hash = test_data[0]["hash"]
        assert len(processed_data[hash].values()) > 1

        hash_value = testrun.get("hash")
        mapped_testrun = processed_data[hash_value]

        for input_key, output_key in processor.key_mappings.items():
            if output_key == 'pr_number' :
                #converted from string to integer during procesisng
                assert mapped_testrun[output_key] in [4295, 4287, 4272]
                continue
            assert testrun[input_key] == mapped_testrun[output_key]


def test_pr_info_key_mapping():
    pr_info = read_test_data('unit_tests/data/pr_info.json')
    processor = PRInfoProcessor()


    for hash_value, pr_data in pr_info.items():
        processor.process((hash_value, pr_data))
        processed_data = processor.get_processed_data()
        mapped_pr_data = processed_data[hash_value]

        for input_key, output_key in processor.key_mappings.items():
            input_value = processor.get_nested_value(pr_data, input_key)
            assert input_value  == mapped_pr_data[output_key]

        assert "diff_url" in mapped_pr_data


def test_pr_info_warning_for_missing_input_key():


    faulty_pr_data = ( "some_hash" , {
        "hash": "some_hash",
        "wrong_key": "value",
    } )
    processor = PRInfoProcessor()

    with pytest.warns(UserWarning, match="Missing input key"):
        processor.process(faulty_pr_data)



def test_testrun_warning_for_missing_input_key():
    faulty_testrun = {
        "hash": "some_hash",
        "wrong_key": "value",
    }
    processor = TestrunProcessor()

    with pytest.warns(UserWarning, match="Missing input key"):
        processor.process(faulty_testrun)





def test_iteration_over_builds():
    loaded_file = read_test_data('unit_tests/data/builds.json')
    build_processor = BuildProcessor("http://x.com/a/b", loaded_file)
    data_combiner = DataCombiner([build_processor])

    combined_data = data_combiner.combine_data_as_dict()

    for item in loaded_file:
        assert item['hash'] in combined_data
        assert item['build_status'] == combined_data[item['hash']]['build_status']