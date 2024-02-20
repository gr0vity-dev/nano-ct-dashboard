from quart import Blueprint, render_template, request
from app.services.ct_results_service import CTResultsService

views = Blueprint('views', __name__)
ct_results_service = CTResultsService()


@views.route('/')
async def show_ct_results():
    response_count = request.args.get('show', default=100, type=int)
    response_count = min(response_count, 1000)

    data = await ct_results_service.get_ct_results(response_count=response_count)
    # Assuming get_ct_results can limit the number of results returned, pass response_count
    # If get_ct_results cannot limit the results, you would slice the data here: data[:response_count]

    return await render_template('ct_results.html', data=data)


@views.route('/<gh_hash>')
async def show_hash_result(gh_hash):
    # Define a filter function
    def filter_func(item): return item['hash'] == gh_hash
    # Pass the filter function
    data = await ct_results_service.get_ct_results(filter_func=filter_func)
    return await render_template('test_results.html', data=data)
