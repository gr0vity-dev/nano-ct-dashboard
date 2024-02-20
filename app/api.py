from quart import Blueprint, jsonify
from app.services.ct_results_service import CTResultsService
from app.services.cache_service import CacheService
from app.secrets import AUTH_PASSWORD

api = Blueprint('api', __name__)
ct_results_service = CTResultsService()
ct_cache = CacheService()


@api.route('/results')
async def get_ct_results():
    combined_data = await ct_results_service.get_ct_results()
    return jsonify(combined_data)


@api.route('/delete_cache/<cache_key>/<auth_key>')
async def delete_cache(cache_key, auth_key):
    await ct_cache.connect()
    # Check if the auth_key is correct
    if auth_key != AUTH_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    # Call the delete method from CTResultsService
    await ct_cache.delete_cache(cache_key)
    return jsonify({"message": "Cache deleted successfully"}), 200
