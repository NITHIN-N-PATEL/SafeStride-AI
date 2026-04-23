# 🛡️ SafeStride AI - Backend v4.0

The intelligent "brain" of the SafeStride AI ecosystem. This backend provides real-time hazard detection, explainable AI insights, emergency SOS management, and OCR services for visually impaired users.

---

##  Key Features

*   ** Explainable Hazard Detection (XAI)**: Uses YOLOv8m to detect 80+ objects with built-in reasoning (e.g., "I see a car because of the wheels and metal body").
*   ** Smart SOS Service**: Manages emergency contacts, logs SOS events, and supports live GPS location tracking.
*   ** OCR Service**: High-accuracy text extraction from signs, books, and labels.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
*   Python 3.10+
*   MongoDB (Local or Atlas Cloud)

### 2. Installation
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory (use `.env.example` as a template):
```env
MONGO_URI=mongodb://localhost:27017/safestride
PORT=8000

# Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

### 4. AI Model Setup
The backend uses the **YOLOv8m** model. The first time you run the app, it will automatically download `yolov8m.pt` (~50MB).

---

##  Running the Backend

Start the server using Python:
```bash
python app.py
```
The server will start at `http://localhost:8000`.

---

## API Endpoints (Brief)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/detect` | POST | Send an image to detect hazards (Add `?heatmap=true` for XAI). |
| `/ocr` | POST | Send an image to extract text. |
| `/sos/trigger` | POST | Trigger an emergency alert. |
| `/sos/location` | POST | Update live GPS coordinates for an active SOS. |
| `/sos/contacts/add`| POST | Register a new emergency contact. |

---

##  Project Structure
*   `app.py`: FastAPI routes and server configuration.
*   `main.py`: AI Detection Service & Explainability logic.
*   `sos_service.py`: SOS and Contact management logic.
*   `ocr_engine.py`: EasyOCR processing logic.
*   `database.py`: MongoDB connection and indexing.
