# app/routes/pois.py

from flask import Blueprint, request, jsonify, current_app
import os
from app.backend.src.pois_api import get_places_by_category

bp = Blueprint('pois', __name__)


@bp.route('/api/pois', methods=['GET'])
def get_pois():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'Kein Stadtname angegeben'}), 400

    data_dir = os.path.join(current_app.root_path, 'backend', 'files', 'city_pois')
    try:
        data = get_places_by_category(city, data_dir=data_dir)
    except FileNotFoundError:
        return jsonify({'error': 'Keine Daten für diese Stadt gefunden'}), 404
    except Exception as exc:
        return jsonify({'error': f'Fehler beim Laden der POIs: {exc}'}), 500

    return jsonify(data)


