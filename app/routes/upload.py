from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
import base64
from datetime import datetime
import cv2
from app.backend import run_pipeline # ocr pipeline

bp = Blueprint('upload', __name__)

@bp.route('/upload', methods=['POST'])
def upload_image():
    try:
        upload_dir = os.path.join(current_app.root_path, 'backend', 'input')
        os.makedirs(upload_dir, exist_ok=True)

        # Um input Ordner leer zu halten, lösche alte Einträge
        for filename in os.listdir(upload_dir):
            if filename == ".gitkeep":
                continue
            file_path = os.path.join(upload_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"❌ Fehler beim Löschen von {file_path}: {e}")

        # Base64-Upload aus Kamera
        if 'photo' in request.form:
            data_url = request.form['photo']
            header, encoded = data_url.split(",", 1)
            image_data = base64.b64decode(encoded)

            filename = f"user_photo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as f:
                f.write(image_data)

        # Datei-Upload
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Leerer Dateiname'}), 400

            filename = f"user_file_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

        else:
            return jsonify({'error': 'Kein Bild empfangen'}), 400

        # Pipeline starten
        result = run_pipeline(file_path, debug=True)
        _, buffer = cv2.imencode('.jpg', result['visualizer_image'])
        visualizer_image_base64 = base64.b64encode(buffer).decode('utf-8')

        response = {
            'city': result['city'],
            'city_backup': result['city_backup'],
            'city_hits': result['city_hits'],
            'visualizer_image': visualizer_image_base64,
            'used_osm': result['used_osm'],
        }
        return jsonify(response)

    except Exception as e:
        print(f"❌ Fehler beim Upload: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/output/<path:filename>')
def serve_output(filename):
    output_dir = os.path.join(current_app.root_path, 'backend', 'output')
    return send_from_directory(output_dir, filename)
