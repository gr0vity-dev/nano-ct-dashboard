from quart import Blueprint, jsonify
from app.services.ct_results_service import CTResultsService

api = Blueprint('api', __name__)
ct_results_service = CTResultsService()


@api.route('/results')
async def get_ct_results():
    combined_data = await ct_results_service.get_ct_results()
    return jsonify(combined_data)
