# SafeStride AI — Backend

Backend server for the SafeStride AI mobile application. Provides real-time hazard detection, pedestrian navigation, OCR text extraction, and SOS emergency services for visually impaired users.

Built with FastAPI, YOLOv8, EasyOCR, OpenRouteService, Twilio, and MongoDB.

## Features

- **Hazard Detection** — Custom-trained YOLOv8 model detecting 80+ COCO objects plus 4 ground-level hazards (pothole, manhole, staircase, road crack). Includes distance estimation, directional awareness, and explainability overlays.
- **Pedestrian Navigation** — Walking-optimized turn-by-turn directions via OpenRouteService. Supports both voice-based destination search and direct coordinate input (hybrid mode for Google Places integration).
- **OCR Text Reader** — Multi-language text extraction using EasyOCR. Supports English, Hindi, Tamil, Telugu, Kannada, Bengali, Marathi, and Nepali. Confidence-filtered to reduce noise.
- **SOS Emergency System** — One-tap emergency alerts via Twilio SMS and automated voice calls. Includes contact management, live location tracking, SOS deduplication, and session resolution.

## Requirements

- Python 3.10+
- MongoDB (local or Atlas)
- Twilio account (for SMS/voice — optional in dev)
- OpenRouteService API key (for navigation)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start the server
python app.py
```

The server starts at `http://localhost:8000`. Interactive API docs are available at `/docs`.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGO_URI` | Yes | MongoDB connection string |
| `ORS_API_KEY` | Yes | OpenRouteService API key |
| `TWILIO_ACCOUNT_SID` | No | Twilio account SID (SMS/voice) |
| `TWILIO_AUTH_TOKEN` | No | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | No | Twilio sender number |
| `SAFESTRIDE_API_KEY` | No | API key for endpoint auth (empty = dev mode) |
| `YOLO_MODEL_PATH` | No | Path to YOLO model (default: `best.pt`) |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/detect` | POST | Upload image for hazard detection |
| `/detect?heatmap=true` | POST | Detection with explainability overlay |
| `/ocr` | POST | Upload image for text extraction |
| `/ocr?language=hi` | POST | OCR with regional language |
| `/navigation/navigate` | POST | Get walking directions |
| `/sos/trigger` | POST | Trigger emergency SOS |
| `/sos/resolve` | POST | Resolve active SOS |
| `/sos/location` | POST | Send live location update |
| `/sos/history/{user_id}` | GET | Fetch SOS event history |
| `/sos/contacts/add` | POST | Add emergency contact |
| `/sos/contacts/remove` | POST | Remove emergency contact |
| `/sos/contacts/{user_id}` | GET | List emergency contacts |

## Project Structure

```
├── app.py              # FastAPI server, routes, middleware
├── main.py             # Detection engine (YOLOv8 + XAI)
├── ocr_engine.py       # OCR service (EasyOCR, multi-language)
├── navigation.py       # Pedestrian navigation (OpenRouteService)
├── sos_service.py      # SOS alerts, contacts, Twilio integration
├── database.py         # MongoDB connection and indexing
├── best.pt             # Custom-trained YOLO model (gitignored)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── .gitignore          # Git exclusions
```

## Detection Model

The backend uses a custom-trained YOLOv8 model (`best.pt`) that detects standard COCO objects along with 4 additional hazard classes relevant to pedestrian safety:

| Hazard | Criticality | Description |
|---|---|---|
| Pothole | High | Ground depressions in walking paths |
| Manhole | High | Open or uncovered manholes |
| Staircase | High | Elevation changes and steps |
| Road Crack | Medium | Surface fractures on sidewalks |

## License

This project is part of the SafeStride AI ecosystem.