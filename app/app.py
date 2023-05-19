from flask import Flask, render_template, jsonify, request
import requests
import json
import datetime
import httpx
import asyncio
from math import ceil

app = Flask(__name__)

ETAGS = {}
# Create a cache for the builds and test runs
BUILDS_CACHE = None
TESTRUNS_CACHE = None
TESTRUN_CACHE = {}
META_DATA = {}


@app.route('/')
async def show_ct_results():
    # Fetch the JSON data
    data = await get_ct_results()
    return render_template('ct_results.html', data=data)

    # # Render the view template with the JSON data
    # page = int(request.args.get('page', 1))
    # per_page = 10  # Number of items per page

    # start_index = (page - 1) * per_page
    # end_index = start_index + per_page
    # paginated_data = data[start_index:end_index]

    # num_pages = ceil(len(data) / per_page)

    # return render_template('ct_results.html',
    #                        data=paginated_data,
    #                        page=page,
    #                        num_pages=num_pages)


@app.route('/api/results')
async def get_ct_results():
    global BUILDS_CACHE, TESTRUNS_CACHE
    builds_url = 'https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/docker_builder/builds.json'
    builds_res = get_with_etag(builds_url)
    if BUILDS_CACHE is None and builds_res.status_code == 200:
        # The resource was modified; parse the new data
        BUILDS_CACHE = builds_res.json()
    elif builds_res.status_code != 304:
        # There was an error; handle it
        return {"error": "Failed to fetch builds"}, builds_res.status_code

    testruns_url = 'https://api.github.com/repos/gr0vity-dev/nano-node-builder/contents/continuous_testing'
    testruns_res = get_with_etag(testruns_url)
    if TESTRUNS_CACHE is None and testruns_res.status_code == 200:
        # The resource was modified; parse the new data
        TESTRUNS_CACHE = testruns_res.json()
    elif testruns_res.status_code != 304:
        # There was an error; handle it
        return {"error": "Failed to fetch test runs"}, testruns_res.status_code

    combined_data = await combine_data(BUILDS_CACHE, TESTRUNS_CACHE)

    return combined_data


# async def get_content(gh_url):
#     if gh_url in TESTRUN_CACHE:
#         return TESTRUN_CACHE[gh_url]

#     async with httpx.AsyncClient() as client:
#         testrun_res = await client.get(gh_url)
#         testrun_res.raise_for_status()
#         TESTRUN_CACHE[gh_url] = testrun_res.json()

#     return TESTRUN_CACHE[gh_url]


async def get_content(gh_url):
    if gh_url in TESTRUN_CACHE:
        return TESTRUN_CACHE[gh_url]

    headers = {}
    if gh_url in ETAGS:
        headers['If-None-Match'] = ETAGS[gh_url]

    async with httpx.AsyncClient() as client:
        response = await client.get(gh_url, headers=headers)
        print(f"httpx.client.get called for {gh_url}")

        if response.status_code == 200:
            TESTRUN_CACHE[gh_url] = response.json()
            ETAGS[gh_url] = response.headers.get('ETag')
        elif response.status_code == 304:
            return TESTRUN_CACHE[gh_url]
        else:
            response.raise_for_status()

    return TESTRUN_CACHE[gh_url]


async def get_testrun(testrun_file):
    return await get_content(testrun_file["download_url"])


async def combine_data(builds, testruns):
    builds_dict = {build['hash']: build for build in builds}

    async def process_testrun(testrun_file):
        if not testrun_file["name"].endswith(".json"):
            return

        # Retrieve testrun data asynchronously
        testrun = await get_testrun(testrun_file)
        test_hash = testrun['hash']
        for testcase in testrun['testcases']:
            if testcase.get("status") == "FAIL":
                testcase["report_url"] = get_report_url(
                    testrun["hash"], testcase["testcase"])

        # if the build exists in builds_dict, add the testcases
        if test_hash in builds_dict:

            overall_started_at = testrun.get('started_at')
            overall_completed_at = testrun.get('completed_at')
            overall_status = testrun.get('overall_status')
            builds_dict[test_hash]['test_status'] = overall_status
            builds_dict[test_hash]['test_started_at'] = overall_started_at
            builds_dict[test_hash]['test_completed_at'] = overall_completed_at
            builds_dict[test_hash]['test_count'] = len(testrun['testcases'])
            builds_dict[test_hash]['fail_count'] = len([
                testcase for testcase in testrun['testcases']
                if testcase['status'] == 'FAIL'
            ])
            builds_dict[test_hash]['pass_count'] = len([
                testcase for testcase in testrun['testcases']
                if testcase['status'] == 'PASS'
            ])
            builds_dict[test_hash]['test_duration'] = get_duration_in_s(
                overall_started_at, overall_completed_at)
            builds_dict[test_hash]['hash_url'] = create_gh_url(
                builds_dict[test_hash])
            builds_dict[test_hash]['testcases'] = testrun['testcases']

    # Execute the processing of testruns concurrently using the event loop
    await asyncio.gather(
        *[process_testrun(testrun_file) for testrun_file in testruns])

    # Convert the dictionary back to a list
    combined_data = list(builds_dict.values())
    filtered_data = [item for item in combined_data if filter_rules(item)]
    filtered_data.sort(key=lambda x: x['built_at'], reverse=True)

    return filtered_data


def get_duration_in_s(started_at, completed_at) -> str:
    duration = None
    if started_at and completed_at:
        duration = str(
            int((datetime.datetime.fromisoformat(completed_at.rstrip('Z')) -
                 datetime.datetime.fromisoformat(
                     started_at.rstrip('Z'))).total_seconds())) + " s"
    return duration


def convert_gh_url_to_api(gh_url):
    nano_repo = "https://github.com/nanocurrency/nano-node"
    api_rep = "https://api.github.com/repos/nanocurrency/nano-node"
    return gh_url.replace(nano_repo, api_rep)


def get_report_url(hash, testcase):
    return f"https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/continuous_testing/{hash}_{testcase}.txt"


# def get_title_body_from_url(url, type):
#     url = convert_gh_url_to_api(url)
#     if type == 'pull_request':

#     elif type == "commit":

#     https://api.github.com/repos/nanocurrency/nano-node/commits/0b73339eb21ac8ce308eafacfee1095768250581
#     ["commit"]["message"]
#     https://api.github.com/repos/nanocurrency/nano-node/pulls/4185


def create_gh_url(data):
    base_url = "https://github.com/nanocurrency/nano-node"
    if data['type'] == 'pull_request':
        # If it's a pull request, link to the pull request
        return f"{base_url}/pull/{data['pull_request']}"
    else:
        # If it's a commit, link to the commit
        return f"{base_url}/commit/{data['hash']}"


def get_with_etag(url):
    headers = {}
    if url in ETAGS:
        headers['If-None-Match'] = ETAGS[url]

    response = requests.get(url, headers=headers)
    print(f"requests.get called for {url}")

    if response.status_code == 200:
        # The resource was modified; cache the new ETag
        ETAGS[url] = response.headers.get('ETag')

    return response


# Define the filtering rules
def filter_rules(item):
    build_status = item.get("build_status")
    created_at_str = item.get("created_at")
    created_at = datetime.datetime.strptime(created_at_str,
                                            "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.datetime.utcnow()
    time_diff = now - created_at

    return build_status and ((build_status == "building"
                              and time_diff.total_seconds() <= 3 * 60 * 60)
                             or build_status == "pass")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    if not loop.is_running():
        loop.create_task(app.run(host='0.0.0.0', port=5000))
        loop.run_forever()
    else:
        loop.create_task(app.run(host='0.0.0.0', port=5000))
    #combined_data()
