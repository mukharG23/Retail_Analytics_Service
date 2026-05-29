import os
import sqlite3
import glob
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from preprocessor import process_image
from metadata_logger import log_metadata
from database import init_db, log_traffic, get_traffic_logs
from congestion import get_congestion_level, get_top_congested_aisles
from yolo_detector import detect_people_threaded
from video_processor import analyze_video_threaded
from traffic_analyzer import analyze_traffic, generate_audit_log
from report_generator import generate_ai_report

app = Flask(__name__)
CORS(app)
init_db()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg','webp'}

VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'videos')
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

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

@app.route('/upload-video', methods=['POST'])
def upload_video():
    print("Video upload route hit!")

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_video(file.filename):
        return jsonify({'error': 'File type not allowed. Use mp4, avi, mov or mkv'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(VIDEO_FOLDER, filename)
    file.save(save_path)

    analyze_video_threaded(save_path, filename, 'Aisle-1')

    return jsonify({
        'message': 'Video uploaded successfully, analysis started in background',
        'filename': filename,
        'note': 'Check /traffic in a minute for results'
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

@app.route('/congestion-stats', methods=['GET'])
def congestion_stats():
    logs = get_traffic_logs()
    low = len([l for l in logs if l['congestion_level'] == 'LOW'])
    medium = len([l for l in logs if l['congestion_level'] == 'MEDIUM'])
    high = len([l for l in logs if l['congestion_level'] == 'HIGH'])
    total = len(logs)
    return jsonify({
        'LOW': low,
        'MEDIUM': medium,
        'HIGH': high,
        'total': total
    }), 200

import cv2
import os
import threading
from ultralytics import YOLO
from database import log_traffic
from congestion import get_congestion_level

FRAMES_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'frames')
ANNOTATED_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'annotated')
SAMPLE_INTERVAL = 2

model = YOLO('yolov8n.pt')

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * SAMPLE_INTERVAL)

    print(f"Video FPS: {fps}, extracting 1 frame every {frame_interval} frames")

    frame_paths = []
    frame_count = 0
    saved_count = 0
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            frame_filename = f"{video_name}_frame_{saved_count:04d}.jpg"
            frame_path = os.path.join(FRAMES_FOLDER, frame_filename)
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            saved_count += 1
        frame_count += 1

    cap.release()
    print(f"Extracted {saved_count} frames from video")
    return frame_paths

def annotate_frame(frame_path, results):
    frame = cv2.imread(frame_path)
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            if int(box.cls[0]) == 0:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 212, 170), 2)
                
                label = f"Person {conf:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(frame, (x1, y1 - 20), (x1 + label_size[0], y1), (0, 212, 170), -1)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    annotated_filename = "latest_annotated.jpg"
    annotated_path = os.path.join(ANNOTATED_FOLDER, annotated_filename)
    cv2.imwrite(annotated_path, frame)
    
    return annotated_path

def analyze_video(video_path, filename, aisle='Aisle-1'):
    print(f"Starting video analysis: {filename}")

    frame_paths = extract_frames(video_path)

    if not frame_paths:
        print("No frames extracted")
        return None

    counts = []

    for i, frame_path in enumerate(frame_paths):
        print(f"Analyzing frame {i+1}/{len(frame_paths)}")
        results = model(frame_path, conf=0.28)

        people_count = 0
        for result in results:
            for cls in result.boxes.cls:
                if int(cls) == 0:
                    people_count += 1

        annotate_frame(frame_path, results)
        counts.append(people_count)
        print(f"Frame {i+1}: {people_count} people")

    if not counts:
        return None

    peak_count = max(counts)
    avg_count = round(sum(counts) / len(counts), 1)
    total_frames = len(counts)

    congestion_level = get_congestion_level(peak_count)
    log_traffic(filename, aisle, peak_count, congestion_level)

    summary = {
        'filename': filename,
        'total_frames_analyzed': total_frames,
        'peak_people_count': peak_count,
        'average_people_count': avg_count,
        'congestion_level': congestion_level
    }

    print(f"Video analysis complete: {summary}")
    return summary

@app.route('/latest-frame', methods=['GET'])
def latest_frame():
    annotated_path = os.path.join(os.path.dirname(__file__), 'uploads', 'annotated', 'latest_annotated.jpg')
    if not os.path.exists(annotated_path):
        return jsonify({'error': 'No annotated frame available'}), 404
    return jsonify({'url': '/annotated/latest_annotated.jpg'}), 200

@app.route('/annotated/<filename>', methods=['GET'])
def serve_annotated(filename):
    from flask import send_from_directory
    annotated_folder = os.path.join(os.path.dirname(__file__), 'uploads', 'annotated')
    return send_from_directory(annotated_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)