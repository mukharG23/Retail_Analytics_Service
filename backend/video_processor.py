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

def annotate_frame(frame_path, results,frame_index):
    frame = cv2.imread(frame_path)
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            if int(box.cls[0]) == 0:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (57, 255, 20), 2)
                
                label = f"Person {conf:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(frame, (x1, y1 - 20), (x1 + label_size[0], y1), (57, 255, 20), -1)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    annotated_filename = f"frame_{frame_index:04d}.jpg"
    annotated_path = os.path.join(ANNOTATED_FOLDER, annotated_filename)
    cv2.imwrite(annotated_path, frame)

    latest_path = os.path.join(ANNOTATED_FOLDER, 'latest_annotated.jpg')
    cv2.imwrite(latest_path, frame)
    
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

        annotate_frame(frame_path, results,i)
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

def analyze_video_threaded(video_path, filename, aisle='Aisle-1'):
    thread = threading.Thread(
        target=analyze_video,
        args=(video_path, filename, aisle)
    )
    thread.start()
    print("Video analysis started in background thread")