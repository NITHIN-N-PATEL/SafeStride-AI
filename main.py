import cv2
import numpy as np
import time
from ultralytics import YOLO
import torch

_original_torch_load = torch.load
def _safe_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _safe_torch_load

MODEL_PATH = "yolov8m.pt"
CONFIDENCE_THRESHOLD = 0.65
FOCAL_LENGTH = 700.0  # Estimated focal length for standard camera

# Known heights for distance estimation (in meters)
OBJECT_HEIGHTS = {
    "person": 1.7, "bicycle": 1.0, "car": 1.5, "motorcycle": 1.2, "airplane": 30.0,
    "bus": 3.0, "train": 4.0, "truck": 3.0, "boat": 2.0, "traffic light": 2.5,
    "fire hydrant": 0.8, "stop sign": 2.1, "parking meter": 1.5, "bench": 0.8,
    "bird": 0.2, "cat": 0.3, "dog": 0.5, "horse": 1.6, "sheep": 1.0, "cow": 1.4,
    "elephant": 3.0, "bear": 1.2, "zebra": 1.4, "giraffe": 4.5, "backpack": 0.5,
    "umbrella": 1.0, "handbag": 0.4, "tie": 0.4, "suitcase": 0.7, "frisbee": 0.05,
    "skis": 1.5, "snowboard": 1.5, "sports ball": 0.2, "kite": 0.6, "baseball bat": 1.0,
    "baseball glove": 0.3, "skateboard": 0.8, "surfboard": 2.0, "tennis racket": 0.7,
    "bottle": 0.25, "wine glass": 0.2, "cup": 0.15, "fork": 0.2, "knife": 0.25,
    "spoon": 0.2, "bowl": 0.15, "banana": 0.2, "apple": 0.1, "sandwich": 0.1,
    "orange": 0.1, "broccoli": 0.2, "carrot": 0.2, "hot dog": 0.15, "pizza": 0.05,
    "donut": 0.05, "cake": 0.2, "chair": 1.0, "couch": 1.0, "potted plant": 0.6,
    "bed": 0.6, "dining table": 0.75, "toilet": 0.8, "tv": 0.6, "laptop": 0.3,
    "mouse": 0.05, "remote": 0.2, "keyboard": 0.15, "cell phone": 0.15,
    "microwave": 0.4, "oven": 0.8, "toaster": 0.3, "sink": 0.9, "refrigerator": 1.8,
    "book": 0.25, "clock": 0.3, "vase": 0.4, "scissors": 0.2, "teddy bear": 0.4,
    "hair drier": 0.25, "toothbrush": 0.2
}
DEFAULT_HEIGHT = 1.0

# Criticality weights for priority alerting (1.0 = normal, 3.0 = high danger)
CRITICALITY = {
    "person": 3.0, "bicycle": 2.5, "car": 3.0, "motorcycle": 3.0, "airplane": 2.0,
    "bus": 3.0, "train": 3.0, "truck": 3.0, "boat": 1.5, "traffic light": 2.5,
    "fire hydrant": 2.0, "stop sign": 3.0, "parking meter": 2.0, "bench": 1.5,
    "bird": 0.5, "cat": 1.5, "dog": 2.2, "horse": 2.0, "sheep": 2.0, "cow": 2.5,
    "elephant": 3.0, "bear": 3.0, "zebra": 2.5, "giraffe": 2.5, "backpack": 1.5,
    "umbrella": 1.2, "handbag": 1.0, "tie": 0.1, "suitcase": 2.0, "frisbee": 0.5,
    "skis": 1.5, "snowboard": 1.5, "sports ball": 2.0, "kite": 0.5, "baseball bat": 1.0,
    "baseball glove": 0.5, "skateboard": 2.5, "surfboard": 1.5, "tennis racket": 0.5,
    "bottle": 1.0, "wine glass": 0.5, "cup": 0.5, "fork": 0.2, "knife": 0.5,
    "spoon": 0.2, "bowl": 0.5, "banana": 1.0, "apple": 0.5, "sandwich": 0.2,
    "orange": 0.5, "broccoli": 0.2, "carrot": 0.2, "hot dog": 0.2, "pizza": 0.2,
    "donut": 0.2, "cake": 0.2, "chair": 1.2, "couch": 1.5, "potted plant": 1.5,
    "bed": 1.5, "dining table": 1.5, "toilet": 1.5, "tv": 1.0, "laptop": 0.5,
    "mouse": 0.2, "remote": 0.2, "keyboard": 0.2, "cell phone": 0.5,
    "microwave": 0.8, "oven": 1.2, "toaster": 0.5, "sink": 1.0, "refrigerator": 1.8,
    "book": 0.5, "clock": 0.5, "vase": 0.8, "scissors": 0.5, "teddy bear": 0.5,
    "hair drier": 0.5, "toothbrush": 0.2
}
DEFAULT_CRITICALITY = 1.0

EXCLUDED_OBJECTS = set()

class AlertManager:
    def __init__(self):
        self.last_alerts = {}  # {label_direction: last_time}
        self.cooldown = 4.5    # Seconds between repeated alerts
        self.urgent_threshold = 1.8 # Distance in meters for urgent override

    def should_alert(self, label, direction, distance):
        key = f"{label}_{direction}"
        now = time.time()
        
        # URGENT OVERRIDE: If it's very close, reduce cooldown significantly
        if distance < self.urgent_threshold:
            if key not in self.last_alerts or (now - self.last_alerts[key]) > 1.2:
                self.last_alerts[key] = now
                return True, "URGENT"
        
        # Standard cooldown
        if key not in self.last_alerts or (now - self.last_alerts[key]) > self.cooldown:
            self.last_alerts[key] = now
            return True, "NORMAL"
            
        return False, None

class DetectionService:
    def __init__(self):
        print(f"Loading model from {MODEL_PATH}...")
        self.model = YOLO(MODEL_PATH)
        self.alert_manager = AlertManager()

    def get_direction(self, cx, frame_w):
        """Calculates granular direction based on center x-coordinate."""
        ratio = cx / frame_w
        if ratio < 0.22: return "far left"
        if ratio < 0.42: return "slightly left"
        if ratio < 0.58: return "straight ahead"
        if ratio < 0.78: return "slightly right"
        return "far right"

    def estimate_distance(self, bbox_h_px, label):
        """Calculates distance in meters using height heuristic."""
        real_h = OBJECT_HEIGHTS.get(label, DEFAULT_HEIGHT)
        if bbox_h_px <= 1: return 99.0
        dist = (real_h * FOCAL_LENGTH) / bbox_h_px
        return round(dist, 1)

    def build_alert_phrase(self, label, distance, direction):
        """Constructs a natural language alert."""
        dist_str = f"{distance} meters" if distance < 10 else "more than 10 meters"
        return f"{label.capitalize()} {dist_str}, {direction}"

    def process_frame(self, frame):
        """
        Processes a single frame (numpy array) and returns detection results.
        """
        frame_h, frame_w, _ = frame.shape
        
        # Run YOLOv8m Inference
        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
        
        detections = []
        alerts_to_speak = []

        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            
            if label in EXCLUDED_OBJECTS:
                continue
                
            conf = float(box.conf[0])
            cx = (x1 + x2) / 2
            bh = y2 - y1
            
            direction = self.get_direction(cx, frame_w)
            distance = self.estimate_distance(bh, label)
            alert_text = self.build_alert_phrase(label, distance, direction)
            
            proximity = "very close" if distance < 2.0 else "close" if distance < 4.5 else ""
            
            crit = CRITICALITY.get(label, DEFAULT_CRITICALITY)
            direction_multiplier = 1.3 if direction == "straight ahead" else 1.0
            danger_score = (crit * direction_multiplier) / max(distance, 0.5)
            
            detections.append({
                "label": label,
                "confidence": round(conf, 3),
                "direction": direction,
                "distance": distance,
                "proximity": proximity,
                "alert_text": alert_text,
                "danger_score": round(danger_score, 2),
                "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)}
            })

        # Sort by Danger Score
        detections.sort(key=lambda d: d['danger_score'], reverse=True)
        
        for d in detections:
            should, alert_type = self.alert_manager.should_alert(d['label'], d['direction'], d['distance'])
            if should:
                prefix = "Careful! " if alert_type == "URGENT" else ""
                alerts_to_speak.append(f"{prefix}{d['alert_text']}")
                if len(alerts_to_speak) >= 2:
                    break

        return {
            "results": detections,
            "alerts": alerts_to_speak,
            "width": int(frame_w),
            "height": int(frame_h)
        }
