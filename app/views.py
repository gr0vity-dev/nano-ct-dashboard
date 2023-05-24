from quart import Blueprint, render_template
from app.services.ct_results_service import CTResultsService

views = Blueprint('views', __name__)
ct_results_service = CTResultsService()


@views.route('/')
async def show_ct_results():
    data = await ct_results_service.get_ct_results()
    return await render_template('ct_results.html', data=data)
