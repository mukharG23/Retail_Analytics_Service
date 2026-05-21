import cv2
import os
from PIL import Image
import numpy as np 

PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'processed')

def process_image(image_path, width=640, height=480):
    pil_image = Image.open(image_path).convert('RGB')
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
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