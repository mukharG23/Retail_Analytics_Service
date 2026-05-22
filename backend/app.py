import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from preprocessor import process_image
from metadata_logger import log_metadata
from database import init_db, log_traffic, get_traffic_logs
from congestion import get_congestion_level
from yolo_detector import detect_people_threaded
from traffic_analyzer import analyze_traffic, generate_audit_log
from report_generator import generate_ai_report

app = Flask(__name__)
CORS(app)
init_db()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg','webp'}

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
    detect_people_threaded(save_path, filename, 'Aisle-1')

    return jsonify({
        'message': 'File uploaded successfully',
        'filename': filename,
        'note': 'People count being processed in background'
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

@app.route('/analyze', methods=['GET'])
def analyze():
    result = analyze_traffic()
    if result is None:
        return jsonify({'error': 'No data to analyze'}), 400
    return jsonify(result), 200

@app.route('/audit', methods=['GET'])
def audit():
    report_path = generate_audit_log()
    if report_path is None:
        return jsonify({'error': 'No data for audit log'}), 400
    return jsonify({'message': 'Audit log generated', 'path': report_path}), 200

    
@app.route('/top-congested', methods=['GET'])
def top_congested():
    logs = get_traffic_logs()
    top = get_top_congested_aisles(logs)
    return jsonify(top), 200

@app.route('/clear', methods=['DELETE'])
def clear_logs():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'database.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM traffic_logs')
    conn.commit()
    conn.close()
    return jsonify({'message': 'All logs cleared successfully'}), 200

@app.route('/delete/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'database.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM traffic_logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Log {log_id} deleted'}), 200

@app.route('/ai-report', methods=['GET'])
def ai_report():
    report_path = generate_ai_report()
    if report_path is None:
        return jsonify({'error': 'No data to generate report'}), 400
    return jsonify({'message': 'AI report generated', 'path': report_path}), 200

if __name__ == '__main__':
    app.run(debug=True)