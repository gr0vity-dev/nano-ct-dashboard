from quart import Quart, make_response, jsonify, request, send_from_directory, Response, render_template

from utils.logger import logger

from processors.ct_processor import DataProcessor
from processors.frontend_processor import format_frontend, format_results
from adapters.leveldb_adapter import LevelDBStorage
from database.sql_processor import SqlProcessor
from adapters.github_client import GitHubClient

import asyncio


app = Quart(__name__)
leveldb_storage = LevelDBStorage("data/leveldb_storage")
sql_processor = SqlProcessor("data/sqlite_storage.db")
gh_client = GitHubClient()

# Update CT data in background to reduce GH Api calls


async def scan_and_process_data():
    processor = DataProcessor(leveldb_storage, sql_processor, gh_client)
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

        formatted_data = format_results(data, median_data)
    else:
        return jsonify({'error': 'Invalid identifier'}), 400

    return jsonify(formatted_data)


@app.route('/api/grouped/', defaults={'count': 50})
@app.route('/api/grouped/<count>')
async def get_grouped_data(count):
    data = sql_processor.fetch_data()
    json_data = format_frontend(data, count)

    # Return a Response Object to keep the order of the dict
    return Response(json_data, mimetype='application/json')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
