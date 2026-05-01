# 🚶‍♂️ SafeStride-AI

**AI-Powered Navigation System for Visually Impaired with Real-Time Obstacle Detection**

[![Flutter](https://img.shields.io/badge/Flutter-3.0+-blue.svg)](https://flutter.dev)
[![Platform](https://img.shields.io/badge/platform-Android%20%7C%20iOS-brightgreen.svg)](https://flutter.dev)
[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/NITHIN-N-PATEL/SafeStride-AI.svg)](https://github.com/NITHIN-N-PATEL/SafeStride-AI/stargazers)

---

## 📖 About The Project

**SafeStride AI** is a revolutionary assistive technology application that empowers **visually impaired individuals** to navigate independently using:

- 🎯 **Real-time AI object detection** (YOLOv8)
- 🎙️ **Voice-first interface** with bilingual support
- ✋ **Intuitive gesture controls** (no visual UI needed)
- 📱 **Smartphone-based** (no expensive hardware required)


> **"Empowering independence through AI"**

---

## ✨ Features

### 🎯 Core Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Object Detection** | Real-time YOLO AI detection of obstacles | ✅ |
| **Voice Feedback** | Text-to-Speech announcements in English & Kannada | ✅ |
| **OCR Reading** | Reads signs, menus, documents aloud | ✅ |
| **Gesture Control** | Double tap, Long press, Swipe up/down | ✅ |
| **Auto Flashlight** | Automatically turns on in dark | ✅ |
| **Low Battery Alert** | Voice + Popup at 20% battery | ✅ |
| **SOS Emergency** | Vibration + Red alert dialog | ✅ |
| **Voice Toggle** | Enable/disable voice feedback | ✅ |

### 🎮 Gesture Controls

| Gesture | Action | Voice Feedback |
|---------|--------|----------------|
| 👆 **Double Tap** | Start / Stop Scanning | "Scanning started/stopped" |
| ⏬ **Long Press** | OCR Text Reading | "Reading text with OCR" |
| ⬆️ **Swipe Up** | SOS Emergency | "Emergency triggered" + Vibration |
| ⬇️ **Swipe Down** | Pause Scanning | "Scanning paused" |

### 🗣️ Voice Commands

| Command | Action |
|---------|--------|
| "Help" / "Gesture instructions" | Repeat all gesture controls |
| "Start" / "Begin" | Start scanning |
| "Stop" / "Pause" | Pause scanning |
| "Status" / "What's around" | Announce current surroundings |
| "SOS" / "Emergency" | Trigger emergency alert |
| "Read text" / "OCR" | Read text from camera |

---

## 📱 Supported Platforms

| Platform | Support | Testing Status |
|----------|---------|----------------|
| **Android Phone** | ✅ Full Support | Production Ready |
| **iPhone/iPad** | ✅ Full Support | Production Ready |
| **Android Emulator** | ⚠️ Limited | Development Only |
| **iOS Simulator** | ⚠️ Limited | Development Only |
| **Web Browser** | ❌ Not Supported | Not Recommended |
| **Desktop** | ❌ Not Supported | Not Recommended |

> ⚠️ **Important:** This app is designed for **PHYSICAL PHONES** with camera, vibration, and touch gestures. It will NOT work properly on laptops or web browsers.

---

## 🚀 Quick Start

### Prerequisites

- **Flutter SDK** (3.0 or higher)
- **Python 3.9+** (for backend)
- **Physical Android/iOS Phone** (Recommended)
- **USB Debugging Enabled** (for Android)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/NITHIN-N-PATEL/SafeStride-AI.git
cd SafeStride-AI

# 2. Navigate to Flutter frontend
cd safestride_frontend

# 3. Get dependencies
flutter pub get

# 4. Connect your phone via USB

# 5. Run the app
flutter run

# 6. Build APK for manual install
flutter build apk --release
# APK location: build/app/outputs/flutter-apk/app-release.apk
