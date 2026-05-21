import threading
from ultralytics import YOLO
from database import log_traffic
from congestion import get_congestion_level

model = YOLO('yolov8n.pt')

def detect_people(image_path, filename, aisle='Aisle-1'):
    results = model(image_path)

    people_count = 0
    for result in results:
        for cls in result.boxes.cls:
            if int(cls) == 0:
                people_count += 1

    congestion_level = get_congestion_level(people_count)
    log_traffic(filename, aisle, people_count, congestion_level)

    print(f"YOLO detected {people_count} people - {congestion_level} congestion")
    return people_count

def detect_people_threaded(image_path, filename, aisle='Aisle-1'):
    thread = threading.Thread(
        target=detect_people,
        args=(image_path, filename, aisle)
    )
    thread.start()
    print("YOLO detection started in background thread")