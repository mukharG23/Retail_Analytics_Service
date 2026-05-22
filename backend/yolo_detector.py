import threading
from ultralytics import YOLO
from inference_sdk import InferenceHTTPClient
from database import log_traffic
from congestion import get_congestion_level
from dotenv import load_dotenv
import os

load_dotenv()

model = YOLO('yolov8n.pt')

cart_client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=os.getenv('ROBOFLOW_API_KEY')
)

CART_WORKSPACE = "marwadi-university"
CART_MODEL_ID = "shopping-cart-6g1zn/2"

def detect_carts(image_path):
    try:
        from PIL import Image as PILImage
        img = PILImage.open(image_path)
        result = cart_client.infer(
            image_path, 
            model_id=CART_MODEL_ID
        )
        print(f"Full Roboflow result: {result}")
        cart_count = len(result.get('predictions', []))
        print(f"Roboflow detected {cart_count} carts")
        return cart_count
    except Exception as e:
        print(f"Cart detection failed: {e}")
        return 0

def detect_people(image_path, filename, aisle='Aisle-1'):
    results = model(image_path,conf=0.6)

    people_count = 0
    for result in results:
        for cls in result.boxes.cls:
            if int(cls) == 0:
                people_count += 1

    cart_count = detect_carts(image_path)

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
    print("YOLO + Cart detection started in background thread")