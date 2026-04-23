import easyocr
import numpy as np
import cv2

class OCRService:
    def __init__(self):
        print("Loading EasyOCR Reader (English)...")
        # Use GPU if available, otherwise CPU
        self.reader = easyocr.Reader(['en'], gpu=True)

    def preprocess_image(self, img_np):
        """Simple preprocessing to improve OCR accuracy"""
        # Convert to grayscale if needed
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # Apply slight blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def extract_text(self, img_np):
        """
        Processes an image (numpy array) and returns extracted text as a single string.
        Now with preprocessing for better accuracy.
        """
        try:
            # Preprocess image
            processed_img = self.preprocess_image(img_np)

            # Extract text
            result = self.reader.readtext(processed_img, detail=0)

            if not result:
                return ""

            # Join all detected text
            full_text = " ".join(result).strip()
            return full_text

        except Exception as e:
            print(f"OCR Error: {e}")
            return "Error reading text."
