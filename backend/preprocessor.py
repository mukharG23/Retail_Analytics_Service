import cv2
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
import os

PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'processed')

def process_image(image_path, width=640, height=480):
    image = cv2.imread(image_path)
    print(f"Trying to read: {image_path}")
    print(f"File exists: {os.path.exists(image_path)}")
    print(f"File size: {os.path.getsize(image_path)}")

    if image is None:
        print(f"Error: Could not read image at {image_path}")
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    resized = cv2.resize(gray, (width, height))

    blurred = cv2.GaussianBlur(resized, (5, 5), 0)

    filename = os.path.basename(image_path)
    save_path = os.path.join(PROCESSED_FOLDER, filename)
    cv2.imwrite(save_path, blurred)

    print(f"Processed image saved to: {save_path}")
    return save_path

def subtract_background(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        print(f"Error: Could not read image at {image_path}")
        return None

    fg_mask = bg_subtractor.apply(image)

    filename = "bg_" + os.path.basename(image_path)
    save_path = os.path.join(PROCESSED_FOLDER, filename)
    cv2.imwrite(save_path, fg_mask)

    print(f"Background subtracted image saved to: {save_path}")
    return save_path