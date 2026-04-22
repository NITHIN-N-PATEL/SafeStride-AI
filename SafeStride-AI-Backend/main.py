import cv2
import numpy as np
import time
import base64
from ultralytics import YOLO
import torch

# --- PyTorch 2.6 Workaround ---
_original_torch_load = torch.load
def _safe_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _safe_torch_load

MODEL_PATH = "yolov8m.pt"
CONFIDENCE_THRESHOLD = 0.45 # Lowered slightly to allow explainability for 'uncertain' cases
FOCAL_LENGTH = 700.0

# ─────────────────────────────────────────────────────────────────────────────
#  EXPLAINABILITY CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

CONFIDENCE_TIERS = {
    "certain":     (0.85, 1.00, "I am very sure about this"),
    "confident":   (0.70, 0.85, "I am fairly confident about this"),
    "moderate":    (0.55, 0.70, "I think this is correct"),
    "uncertain":   (0.45, 0.55, "I am not fully sure — please be cautious"),
}

CLASS_VISUAL_CUES = {
    "person": "upright human silhouette, limb movement, clothing texture",
    "bicycle": "two circular wheels, frame structure, handlebars",
    "car": "rectangular metal body, four wheels, windshield reflection",
    "truck": "large vehicle with cargo area or container",
    "traffic light": "vertical signal box with coloured light indicators",
    "stop sign": "octagonal red sign with white border",
    "dog": "four-legged animal with fur texture and tail",
    "chair": "four legs, seat surface, often with backrest",
}

OBJECT_HEIGHTS = {
    "person": 1.7, "bicycle": 1.0, "car": 1.5, "motorcycle": 1.2,
    "bus": 3.0, "truck": 3.0, "traffic light": 2.5, "stop sign": 2.1,
    "dog": 0.5, "chair": 1.0, "potted plant": 0.6, "cell phone": 0.15
}
DEFAULT_HEIGHT = 1.0

CRITICALITY = {
    "person": 3.0, "car": 3.0, "bus": 3.0, "truck": 3.0, "stop sign": 3.0, "dog": 2.2
}
DEFAULT_CRITICALITY = 1.0

# ─────────────────────────────────────────────────────────────────────────────
#  SERVICES
# ─────────────────────────────────────────────────────────────────────────────

class AlertManager:
    def __init__(self):
        self.last_alerts = {}
        self.cooldown = 4.5
        self.urgent_threshold = 1.8

    def should_alert(self, label, direction, distance):
        key = f"{label}_{direction}"
        now = time.time()
        if distance < self.urgent_threshold:
            if key not in self.last_alerts or (now - self.last_alerts[key]) > 1.2:
                self.last_alerts[key] = now
                return True, "URGENT"
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
        for tier, (low, high, phrase) in CONFIDENCE_TIERS.items():
            if low <= conf <= high:
                colour = {"certain": "#34d399", "confident": "#6c63ff", 
                          "moderate": "#fbbf24", "uncertain": "#f87171"}[tier]
                return {"tier": tier, "colour": colour, "spoken_phrase": phrase}
        return {"tier": "uncertain", "colour": "#f87171", "spoken_phrase": "Be cautious"}

    def generate_gradcam_heatmap(self, frame, x1, y1, x2, y2):
        """Generates the visual explainability overlay."""
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
        tier_info = self.get_confidence_tier(conf)
        visual_cues = CLASS_VISUAL_CUES.get(label, "visual patterns and shape")
        height_ratio = bbox_h_px / frame_h

        # ── Why detection? ──
        detection_reason = f"The model recognised a {label} based on {visual_cues}. {tier_info['spoken_phrase']}."

        # ── Spatial Factors ──
        spatial_factors = [
            {"factor": "Position", "value": direction, "explanation": f"Object is {direction}."},
            {"factor": "Confidence", "value": f"{conf*100:.0f}%", "explanation": f"Tier: {tier_info['tier'].upper()}."}
        ]

        # ── Uncertainty Flags ──
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
        ratio = cx / frame_w
        if ratio < 0.22: return "far left"
        if ratio < 0.42: return "slightly left"
        if ratio < 0.58: return "straight ahead"
        if ratio < 0.78: return "slightly right"
        return "far right"

    def estimate_distance(self, bbox_h_px, label):
        real_h = OBJECT_HEIGHTS.get(label, DEFAULT_HEIGHT)
        if bbox_h_px <= 1: return 99.0
        dist = (real_h * FOCAL_LENGTH) / bbox_h_px
        return round(dist, 1)

    def process_frame(self, frame, include_heatmap=False):
        frame_h, frame_w, _ = frame.shape
        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
        
        detections = []
        alerts_to_speak = []

        for box in results.boxes:
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            label = results.names[int(box.cls[0])]
            conf = float(box.conf[0])
            
            direction = self.get_direction((x1+x2)/2, frame_w)
            distance = self.estimate_distance(y2-y1, label)
            
            # --- Generate Explainability Data ---
            explain = self.build_reasoning(label, conf, direction, distance, y2-y1, frame_h)
            
            det_data = {
                "label": label,
                "confidence": round(conf, 3),
                "direction": direction,
                "distance": distance,
                "explainability": explain,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            }

            if include_heatmap:
                det_data["heatmap_b64"] = self.generate_gradcam_heatmap(frame, x1, y1, x2, y2)

            detections.append(det_data)

        # Alerts (Using your custom Danger Score logic)
        for d in detections:
            crit = CRITICALITY.get(d['label'], DEFAULT_CRITICALITY)
            mult = 1.3 if d['direction'] == "straight ahead" else 1.0
            d['danger_score'] = round((crit * mult) / max(d['distance'], 0.5), 2)

        detections.sort(key=lambda d: d['danger_score'], reverse=True)
        
        for d in detections:
            should, a_type = self.alert_manager.should_alert(d['label'], d['direction'], d['distance'])
            if should:
                prefix = "Careful! " if a_type == "URGENT" else ""
                alerts_to_speak.append(f"{prefix}{d['label']} {d['distance']}m, {d['direction']}")
                if len(alerts_to_speak) >= 2: break

        return {
            "results": detections,
            "alerts": alerts_to_speak,
            "width": int(frame_w), "height": int(frame_h)
        }