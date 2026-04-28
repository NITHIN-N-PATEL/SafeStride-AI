import cv2
import numpy as np
import time
import base64
import os
from pathlib import Path
from ultralytics import YOLO
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("YOLO_MODEL_PATH", str(Path(__file__).parent / "best.pt"))
CONFIDENCE_THRESHOLD = 0.50
FOCAL_LENGTH = 700.0
MAX_DISPLAY_DISTANCE = 15.0


# Explainability configuration

CONFIDENCE_TIERS = {
    "certain":     (0.85, 1.00, "I am very sure about this"),
    "confident":   (0.70, 0.85, "I am fairly confident about this"),
    "moderate":    (0.55, 0.70, "I think this is correct"),
    "uncertain":   (0.45, 0.55, "I am not fully sure, please be cautious"),
}

CLASS_VISUAL_CUES = {
    "person": "upright human silhouette, limb movement, clothing texture",
    "bicycle": "two circular wheels, frame structure, handlebars",
    "car": "rectangular metal body, four wheels, windshield reflection",
    "motorcycle": "two wheels, engine block, handlebars",
    "bus": "large vehicle with cargo area or container",
    "truck": "large vehicle with cargo area or container",
    "traffic light": "vertical signal box with coloured light indicators",
    "stop sign": "octagonal red sign with white border",
    "dog": "four-legged animal with fur texture and tail",
    "chair": "four legs, seat surface, often with backrest",
    "cell phone": "small rectangular handheld device",
    # Custom hazard classes
    "pothole": "dark circular or irregular depression in the road surface",
    "manhole": "circular metal cover or open hole on the sidewalk",
    "staircase": "series of horizontal steps with elevation changes",
    "roadcrack": "visible fracture lines or splits on the road surface",
}

# Known real-world heights for distance estimation (meters)
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
    "hair drier": 0.25, "toothbrush": 0.2,
    # Custom hazard classes
    "pothole": 0.15, "manhole": 0.6, "staircase": 2.0, "roadcrack": 0.05,
}
DEFAULT_HEIGHT = 1.0

# Criticality weights for priority alerting
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
    "hair drier": 0.5, "toothbrush": 0.2,
    # Custom hazard classes (high danger for pedestrians)
    "pothole": 3.0, "manhole": 3.0, "staircase": 3.0, "roadcrack": 2.5,
}
DEFAULT_CRITICALITY = 1.0

EXCLUDED_OBJECTS = set()

class AlertManager:
    def __init__(self):
        self.last_alerts = {}  # {label_direction: last_time}
        self.cooldown = 4.5    # Seconds between repeated alerts
        self.urgent_threshold = 1.8 # Distance in meters for urgent override
        self.cleanup_interval = 60.0  # Purge stale entries older than this

    def _cleanup(self):
        """Remove entries older than cleanup_interval to prevent memory leaks."""
        now = time.time()
        stale_keys = [k for k, t in self.last_alerts.items() if (now - t) > self.cleanup_interval]
        for k in stale_keys:
            del self.last_alerts[k]

    def should_alert(self, label, direction, distance):
        key = f"{label}_{direction}"
        now = time.time()

        # Periodically clean up stale entries
        if len(self.last_alerts) > 50:
            self._cleanup()
        
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

    def get_confidence_tier(self, conf: float) -> dict:
        """Categorizes detection confidence into meaningful tiers."""
        for tier, (low, high, phrase) in CONFIDENCE_TIERS.items():
            if low <= conf <= high:
                colour = {"certain": "#34d399", "confident": "#6c63ff", 
                          "moderate": "#fbbf24", "uncertain": "#f87171"}[tier]
                return {"tier": tier, "colour": colour, "spoken_phrase": phrase}
        return {"tier": "uncertain", "colour": "#f87171", "spoken_phrase": "Be cautious"}

    def generate_attention_overlay(self, frame, x1, y1, x2, y2):
        """Gaussian attention overlay centered on the detection bounding box."""
        h, w = frame.shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        sigma_x, sigma_y = max((x2 - x1) / 2.5, 1), max((y2 - y1) / 2.5, 1)
        
        xs, ys = np.arange(w), np.arange(h)
        xg, yg = np.meshgrid(xs, ys)
        gaussian = np.exp(-(((xg - cx)**2)/(2*sigma_x**2) + ((yg - cy)**2)/(2*sigma_y**2)))
        
        heatmap = (gaussian * 255).astype(np.uint8)
        coloured = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        blended = cv2.addWeighted(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), 0.6, coloured, 0.4, 0)
        _, buffer = cv2.imencode(".png", blended)
        return base64.b64encode(buffer).decode("utf-8")

    def build_reasoning(self, label, conf, direction, distance, bbox_h_px, frame_h):
        """Constructs explainability metadata for a detection."""
        tier_info = self.get_confidence_tier(conf)
        visual_cues = CLASS_VISUAL_CUES.get(label, "visual patterns and shape")
        height_ratio = bbox_h_px / frame_h

        detection_reason = f"The model recognised a {label} based on {visual_cues}. {tier_info['spoken_phrase']}."

        spatial_factors = [
            {"factor": "Position", "value": direction, "explanation": f"Object is {direction}."},
            {"factor": "Confidence", "value": f"{conf*100:.0f}%", "explanation": f"Tier: {tier_info['tier'].upper()}."}
        ]

        uncertainty_flags = []
        if conf < 0.60: uncertainty_flags.append("Low confidence — lighting or occlusion might affect accuracy.")
        if height_ratio > 0.7: uncertainty_flags.append("Object is very close — edges may be cropped.")

        return {
            "detection_reason": detection_reason,
            "spatial_factors": spatial_factors,
            "uncertainty_flags": uncertainty_flags,
            "confidence_tier": tier_info,
            "spoken_explanation": f"{label.capitalize()} {direction}. {tier_info['spoken_phrase']}."
        }

    def get_direction(self, cx, frame_w):
        """Calculates granular direction based on center x-coordinate."""
        ratio = cx / frame_w
        if ratio < 0.22: return "far left"
        if ratio < 0.42: return "slightly left"
        if ratio < 0.58: return "straight ahead"
        if ratio < 0.78: return "slightly right"
        return "far right"

    def estimate_distance(self, bbox_h_px, label):
        """Calculates distance in meters using height heuristic. Capped at MAX_DISPLAY_DISTANCE."""
        real_h = OBJECT_HEIGHTS.get(label, DEFAULT_HEIGHT)
        if bbox_h_px <= 1: return MAX_DISPLAY_DISTANCE
        dist = (real_h * FOCAL_LENGTH) / bbox_h_px
        return round(min(dist, MAX_DISPLAY_DISTANCE), 1)

    def process_frame(self, frame, include_heatmap=False):
        """
        Processes a single frame (numpy array) and returns detection results with explainability.
        """
        frame_h, frame_w, _ = frame.shape
        
        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
        
        detections = []
        alerts_to_speak = []

        for box in results.boxes:
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            
            if label in EXCLUDED_OBJECTS:
                continue
                
            conf = float(box.conf[0])
            cx = (x1 + x2) / 2
            bh = y2 - y1
            
            direction = self.get_direction(cx, frame_w)
            distance = self.estimate_distance(bh, label)
            
            explain = self.build_reasoning(label, conf, direction, distance, bh, frame_h)
            
            proximity = "out of range" if distance >= MAX_DISPLAY_DISTANCE else "very close" if distance < 2.0 else "close" if distance < 4.5 else ""
            
            crit = CRITICALITY.get(label, DEFAULT_CRITICALITY)
            direction_multiplier = 1.3 if direction == "straight ahead" else 1.0
            danger_score = (crit * direction_multiplier) / max(distance, 0.5)
            
            det_data = {
                "label": label,
                "confidence": round(conf, 3),
                "direction": direction,
                "distance": distance,
                "proximity": proximity,
                "danger_score": round(danger_score, 2),
                "explainability": explain,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            }

            if include_heatmap:
                det_data["heatmap_b64"] = self.generate_attention_overlay(frame, x1, y1, x2, y2)
                det_data["xai_method"] = "gaussian_proxy"

            detections.append(det_data)

        detections.sort(key=lambda d: d['danger_score'], reverse=True)
        
        for d in detections:
            should, alert_type = self.alert_manager.should_alert(d['label'], d['direction'], d['distance'])
            if should:
                prefix = "Careful! " if alert_type == "URGENT" else ""
                alerts_to_speak.append(f"{prefix}{d['label'].capitalize()} {d['distance']} meters, {d['direction']}")
                if len(alerts_to_speak) >= 2:
                    break

        return {
            "results": detections,
            "alerts": alerts_to_speak,
            "width": int(frame_w),
            "height": int(frame_h)
        }
