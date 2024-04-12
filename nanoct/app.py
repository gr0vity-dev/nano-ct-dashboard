from quart import Quart, make_response, jsonify, request, send_from_directory, Response, render_template

from utils.logger import logger

from data_processor import DataProcessor
from storage.leveldb_adapter import LevelDBStorage
from interfaces.sql_processor import SqlProcessor

from collections import defaultdict, OrderedDict
import asyncio
import json

app = Quart(__name__)
leveldb_storage = LevelDBStorage("data/leveldb_storage")
sql_processor = SqlProcessor("data/sqlite_storage.db")


async def scan_and_process_data():
    processor = DataProcessor(leveldb_storage, sql_processor)
    while True:
        print("Scanning for new data...")
        try:
            await processor.process_and_store_data()
            print("Data updated successfully")
        except Exception as e:
            print(f"Error updating data: {str(e)}")
        await asyncio.sleep(300)  # Sleep for 5 minutes


@app.before_serving
async def start_background_task():
    app.add_background_task(scan_and_process_data)


@app.route('/', defaults={'count': 50})
@app.route('/<int:count>')
async def index(count):
    # Render the template with the default count of 50
    grouped_data = await get_grouped_data(count)
    data = await grouped_data.get_json()
    return await render_template('pr_overview.html', pr_data=data)


@app.route('/details/<hash_value>')
async def details_by_hash(hash_value):
    hash_data = sql_processor.fetch_data(hash_value)
    results_data = sql_processor.fetch_test_data(hash_value)
    median_duration = sql_processor.fetch_median_testduration()
    return await render_template('test_details.html',
                                 test_results=results_data,
                                 hash_data=hash_data[0],
                                 median_duration=median_duration)


@app.route('/api/data/', defaults={'identifier': None})
@app.route('/api/data/<identifier>')
async def fetch_data(identifier):
    params = {}
    if identifier:
        if len(identifier) == 40:
            params['hash_value'] = identifier
        elif identifier.isdigit() and len(identifier) <= 5:
            params['pull_request'] = identifier
        else:
            return jsonify({'error': 'Invalid identifier'}), 400

    data = sql_processor.fetch_data(**params)
    if not data:
        return jsonify({'error': 'Data not found'}), 404

    return jsonify(data)


@app.route('/api/results/<hash_value>')
async def fetch_test_data(hash_value):

    if len(hash_value) == 40:
        data = sql_processor.fetch_test_data(hash_value=hash_value)
        median_data = sql_processor.fetch_median_testduration()

        # Extend with min max avh and median duration
        for test in data:
            testcase_data = median_data.get(test['testcase'], {})
            median_duration = testcase_data.get('median_duration')
            for key, value in testcase_data.items():
                test[key] = value

            if median_duration is not None:
                # Calculate deviation if median duration exists
                test['deviation_from_median'] = test['duration'] - median_duration
            else:
                # Indicate absence of median data
                test['deviation_from_median'] = 'No median data available'
    else:
        return jsonify({'error': 'Invalid identifier'}), 400

    return jsonify(data)


@app.route('/api/grouped/', defaults={'count': 50})
@app.route('/api/grouped/<count>')
async def get_grouped_data(count):
    data = sql_processor.fetch_data()
    grouped_data = defaultdict(list)

    pr_order = []  # To track the order of pull requests as they first appear
    for entry in data:
        pr = str(entry['pull_request'])
        if pr.isdigit():  # Check if pr is numeric
            if pr not in pr_order:
                pr_order.append(pr)
            grouped_data[pr].append(entry)

    # Process grouped data to create the desired structure, maintaining pull request order
    structured_data = OrderedDict()  # To maintain the order of insertion
    for pr in pr_order[:count]:
        entries = grouped_data[pr]
        # Find the first entry with a non-null values
        author = next((entry.get('author')
                      for entry in entries if entry.get('author')), '')
        avatar = next((entry.get('avatar')
                      for entry in entries if not "/.png" in entry.get('avatar')), '')
        revision = next((entry.get('revision')
                         for entry in entries if entry.get('revision')), '')
        branch = next((entry.get('branch')
                       for entry in entries if not "/None" in entry.get('branch')), '')
        pr_url = next((entry.get('pr_url')
                       for entry in entries if entry.get('pr_url')), '')

        header_data = {
            'pr_number': pr,
            'author': author,
            'avatar': avatar,
            'branch': branch,
            'pr_url': pr_url,
            'overall_status': entries[0]['overall_status'],
            'current_revision': revision,
            'last_modified': entries[0]['last_modified'],
            'merge_duration': entries[0]['duration_in_days'],
            'merged': entries[0].get('matching_commit'),
            'title': entries[0].get('title'),
        }

        structured_data[pr] = {
            'header': header_data,
            'entries': entries
        }
    json_data = json.dumps(structured_data)

    # Return a response to keep the order of the dict
    return Response(json_data, mimetype='application/json')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
