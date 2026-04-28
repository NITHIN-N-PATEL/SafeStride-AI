import cv2
from ocr_engine import OCRService

# 1. Provide your image path here
IMAGE_PATH = r"C:\SafeStride AI\SafeStride-AI\Screenshot 2026-04-23 183627.png"

def run_test():
    # 2. Initialize the engine
    service = OCRService()
    
    # 3. Load image
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print(f"Error: Could not find image at {IMAGE_PATH}")
        return

    # 4. Extract and Print
    text = service.extract_text(img)
    print("\n--- OCR OUTPUT ---")
    print(text)
    print("------------------")

if __name__ == "__main__":
    run_test()
