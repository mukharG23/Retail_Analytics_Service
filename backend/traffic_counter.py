import cv2
import os

MIN_AREA = 800

def count_people(processed_image_path):
    image = cv2.imread(processed_image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        print(f"Error: Could not read image at {processed_image_path}")
        return 0

    _, thresh = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY_INV)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    people = [c for c in contours if cv2.contourArea(c) > MIN_AREA]

    count = len(people)
    print(f"People count: {count}")
    return count