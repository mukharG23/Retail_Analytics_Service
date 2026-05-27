import cv2
import os
import threading
from yolo_detector import detect_people
from database import log_traffic
from congestion import get_congestion_level

FRAMES_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'frames')
SAMPLE_INTERVAL = 3  # extract 1 frame every 3 seconds

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

def analyze_video(video_path, filename, aisle='Aisle-1'):
    print(f"Starting video analysis: {filename}")

    frame_paths = extract_frames(video_path)

    if not frame_paths:
        print("No frames extracted")
        return None

    counts = []
    from ultralytics import YOLO
    model = YOLO('yolov8n.pt')
    for i, frame_path in enumerate(frame_paths):
        print(f"Analyzing frame {i+1}/{len(frame_paths)}")
        results = model(frame_path, conf=0.28)

        people_count = 0
        for result in results:
            for cls in result.boxes.cls:
                if int(cls) == 0:
                    people_count += 1

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