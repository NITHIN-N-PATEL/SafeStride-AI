# SafeStride AI Backend Guide

Welcome to the SafeStride AI Backend documentation! This project follows a modular architecture to separate the API orchestration from the core AI processing engines.

## 📂 Modular Architecture

The backend is split into three main components:

1.  **`app.py` (The Orchestrator):**
    *   This is the **Main Entry Point**.
    *   It handles the FastAPI server, CORS configuration, and API routing.
    *   It manages the HTTP requests and delegates the actual processing to the specialized services.

2.  **`main.py` (Detection Service):**
    *   Encapsulates all **Object Detection** logic.
    *   Loads the YOLOv8 model and handles coordinate calculations, distance estimation, and danger scoring.
    *   **Tweaking Logic:** Modify `OBJECT_HEIGHTS` or `CRITICALITY` in this file to adjust how objects are detected and prioritized.

3.  **`ocr_engine.py` (OCR Service):**
    *   Handles **Optical Character Recognition** using EasyOCR.
    *   Initialized separately to keep the heavy OCR models isolated from the detection pipeline.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9 - 3.12
- A working webcam (for testing)

### 2. Installation
Open your terminal in the root directory and run:

```bash
# Install dependencies
pip install -r requirements.txt
```

*(Note: PyTorch will be installed automatically. For GPU acceleration, visit [pytorch.org](https://pytorch.org/) to install the CUDA version).*

### 3. Running the Server

**Always run `app.py` to start the backend:**

```bash
python app.py
```

The server will start at `http://0.0.0.0:8000`.

---

## 📡 API Endpoints

### 1. Object Detection (`POST /detect`)
*Consumes a frame and returns a list of detected objects.*
- **Input:** Multipart form data with a `file` field (JPEG/PNG).
- **Processing (via `main.py`):** 
  - Runs YOLOv8m Inference.
  - Heuristic-based distance estimation.
  - Priority alerting via "Danger Scores".
- **Output:** JSON containing `results`, `width`, and `height`.

### 2. Optical Character Recognition (`POST /ocr`)
*Consumes an image and returns extracted text.*
- **Input:** Multipart form data with a `file` field. Optional: `flip=true` for mirrored webcams.
- **Processing (via `ocr_engine.py`):** 
  - Image normalization and EXIF handling.
  - EasyOCR text extraction.
- **Output:** JSON containing `text` and `char_count`.

---

## 🛠 Backend Developer Tips
- **Performance:** If the detection is slow on your CPU, change the model in `main.py` from `yolov8m.pt` to `yolov8n.pt` (Nano).
- **Thresholds:** Adjust `CONFIDENCE_THRESHOLD` in `main.py` to filter out low-confidence detections.
- **Mirroring:** The backend provides a `flip` parameter for OCR, but for detection, coordinate mirroring is handled by the **Frontend** based on the user's camera type.