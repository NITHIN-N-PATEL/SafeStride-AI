import easyocr
import numpy as np
import cv2
import torch

# EasyOCR requires separate readers per script family.
# Each group pairs one regional script with English.

LANGUAGE_GROUPS = {
    "en":  ["en"],                 # English only (default)
    "hi":  ["hi", "en"],           # Hindi + English
    "ta":  ["ta", "en"],           # Tamil + English
    "te":  ["te", "en"],           # Telugu + English
    "kn":  ["kn", "en"],           # Kannada + English
    "bn":  ["bn", "en"],           # Bengali + English
    "mr":  ["mr", "en"],           # Marathi + English
    "ne":  ["ne", "en"],           # Nepali + English
}

# Minimum confidence threshold — results below this are considered noise
MIN_CONFIDENCE = 0.4


class OCRService:
    def __init__(self):
        gpu_available = torch.cuda.is_available()
        print(f"[OCR] Device: {'GPU (CUDA)' if gpu_available else 'CPU'} — {'Fast' if gpu_available else 'Slow cold starts expected'}")
        print(f"[OCR] Supported languages: {list(LANGUAGE_GROUPS.keys())}")

        self.gpu = gpu_available
        self.readers = {}

        # Pre-load English reader at startup
        self.readers["en"] = easyocr.Reader(["en"], gpu=self.gpu)

    def _get_reader(self, lang: str) -> easyocr.Reader:
        """Returns a reader for the given language, loading lazily on first use."""
        if lang not in LANGUAGE_GROUPS:
            print(f"[OCR] Unsupported language '{lang}', falling back to English")
            lang = "en"

        if lang not in self.readers:
            langs = LANGUAGE_GROUPS[lang]
            print(f"[OCR] Loading reader for: {langs} (first-time load)...")
            self.readers[lang] = easyocr.Reader(langs, gpu=self.gpu)
            print(f"[OCR] Reader for {langs} ready.")

        return self.readers[lang]

    def preprocess_image(self, img_np):
        """Grayscale + light blur. Skips hard binarization to preserve low-contrast text."""
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        return cv2.GaussianBlur(gray, (3, 3), 0)

    def extract_text(self, img_np, language: str = "en"):
        """Run OCR on an image array and return filtered text."""
        try:
            reader = self._get_reader(language)

            # Preprocess image
            processed_img = self.preprocess_image(img_np)

            results = reader.readtext(processed_img, detail=1)

            if not results:
                return ""

            filtered = [item[1] for item in results if item[2] >= MIN_CONFIDENCE]

            if not filtered:
                return ""

            full_text = " ".join(filtered).strip()
            return full_text

        except Exception as e:
            print(f"[OCR] Error: {e}")
            return "Error reading text."
