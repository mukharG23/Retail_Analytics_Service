import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from preprocessor import process_image, subtract_background
from metadata_logger import log_metadata
from traffic_counter import count_people
from database import init_db, log_traffic, get_traffic_logs
from congestion import get_congestion_level, get_top_congested_aisles

app = Flask(__name__)
CORS(app)
init_db()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    log_metadata(filename, save_path)
    processed_path = process_image(save_path)
    count = count_people(processed_path)
    congestion_level = get_congestion_level(count)
    log_traffic(filename, 'Aisle-1', count, congestion_level)

    return jsonify({
        'message': 'File uploaded successfully',
        'filename': filename,
        'people_count': count,
        'congestion_level': congestion_level
    }), 200
@app.route('/traffic', methods=['GET'])
def traffic_logs():
    logs = get_traffic_logs()
    return jsonify(logs), 200

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    log_metadata(filename, save_path)
    processed_path = process_image(save_path)
    count=count_people(processed_path)
    congestion_level=get_congestion_level(count)
    log_traffic(filename,'Aisle-1',count,congestion_level)

    return jsonify({'message': 'File uploaded successfully', 'filename': filename,'people_count': count,'congestion count':congestion_level}), 200

@app.route('/top-congested', methods=['GET'])
def top_congested():
    logs = get_traffic_logs()
    top = get_top_congested_aisles(logs)
    return jsonify(top), 200

if __name__ == '__main__':
    app.run(debug=True)