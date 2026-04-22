import easyocr
import numpy as np

class OCRService:
    def __init__(self):
        print("Loading EasyOCR Reader (English)...")
        self.reader = easyocr.Reader(['en'])

    def extract_text(self, img_np):
        """
        Processes an image (numpy array) and returns extracted text as a single string.
        """
        try:
            
            result = self.reader.readtext(img_np, detail=0)
            
            if not result:
                return ""
            full_text = " ".join(result)
            return full_text
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return "Error reading text."
