# SafeStride: 84-Class Hazard Detection Model (YOLOv8)

This repository contains the training and fine-tuning pipeline for the **SafeStride** navigation system. The model is designed to detect 80 standard COCO objects and 4 custom specialized hazards to assist visually impaired individuals.

##  Model Performance (v1.0)
- **Base Model:** YOLOv8m
- **Overall Accuracy (mAP50):** 53.6%
- **Highlights:** 
  - **Stairs:** 99.5% Accuracy
  - **Open Manholes:** 98.7% Accuracy
  - **Potholes:** 72.2% Accuracy
  - **Road Cracks:** 38.7% Accuracy

##  Class IDs (84 Classes)
- **0 - 79:** Standard COCO Classes (Person, Car, Dog, etc.)
- **80:** Pothole
- **81:** Road Crack
- **82:** Open Manhole
- **83:** Stairs


### 2. Dataset Setup
1. **Download Dataset:** `[https://drive.google.com/file/d/1PaJ7l1T3-GQYPm73cBp6wb18f-VtaJX_/view?usp=drive_link]`
2. **Download Weights:**
   - **[best.pt](https://drive.google.com/file/d/1Yt2NvBVvqwdj6zz8oe2EbOSHUwdFhmw6/view?usp=drive_link):** Use for testing, inference, or starting fresh fine-tuning.
   - **[last.pt](https://drive.google.com/file/d/1CDZHs53MBnWCq_PwmdkBgfwoN44J3FJ-/view?usp=drive_link):** Use ONLY to resume the interrupted training run.


## Project Structure
- `p5_train_yolov8.ipynb`: Main training logic and monitoring.
- `final_training_config.yaml`: Dataset mapping and class definitions.
- `test.py`: Quick inference script for testing individual images.
- `requirements.txt`: Python environment dependencies.
