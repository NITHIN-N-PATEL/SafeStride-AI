**SMART Goals**

**Specific**
Develop a mobile-based AI application (SafeStride AI) that assists visually impaired individuals by detecting obstacles in real time and providing voice-based navigation support.

**Measurable**
Achieve object detection accuracy of ≥ 80%
Maintain response time < 1 second
Provide distance estimation within ±1 meter
Deliver clear voice alerts for detected objects

**Achievable**
Use lightweight models such as YOLO to ensure real-time performance on mobile devices without requiring high-end hardware.

**Relevant**
Addresses real-world navigation challenges faced by visually impaired individuals, improving safety, accessibility, and independence.

**Time-bound**
Complete development, testing, and deployment within the academic timeline, with further improvements planned in future phases. 

<img width="1192" height="797" alt="image" src="https://github.com/user-attachments/assets/a0e8695b-51fe-4ed9-a6ae-d25cc393659f" />

**Step by Step SetUp**

**Overview**
This project presents a mobile-based assistive system designed to help visually impaired individuals navigate their surroundings safely. The application uses AI-powered object detection, OCR, and voice guidance to provide real-time feedback and improve user independence.
________________________________________
**Problem Statement**
Visually impaired individuals face challenges in:
•	Detecting obstacles
•	Reading text from surroundings
•	Navigating safely without assistance
________________________________________
**Proposed Solution**
The system uses a combination of computer vision and mobile technologies to:
•	Detect objects in real time using YOLOv8
•	Read text using OCR
•	Provide voice-based alerts and instructions
•	Enable emergency assistance through SOS feature
________________________________________
 **Features**
•	Real-time Object Detection
•	OCR (Text Recognition)
•	Voice Guidance (Text-to-Speech)
•	Gesture-Based Controls
•	SOS Emergency Alert System
•	Accessible UI for visually impaired users
________________________________________
**System Architecture**
Camera → YOLO Model → Processing → Voice Output
                      ↓
                    OCR
                      ↓
                     SOS
________________________________________
**Technologies Used**
•	Flutter (Frontend)
•	Python (Backend)
•	YOLOv8 (Object Detection)
•	OpenCV
•	Tesseract OCR
•	Text-to-Speech (TTS)
•	Speech Recognition
________________________________________
**Setup Instructions**
1. Clone the Repository
git clone https://github.com/NITHIN-N-PATEL/SafeStride-AI.git
cd SafeStride-AI
________________________________________
2. Navigate to Frontend
cd safestride_frontend
________________________________________
3. Install Dependencies
flutter pub get
________________________________________
4. Connect Device
•	Connect your Android phone via USB
•	Enable USB Debugging
________________________________________
5. Run the App
flutter run
________________________________________
6. Build APK (Optional)
flutter build apk --release
APK Location:
build/app/outputs/flutter-apk/app-release.apk
________________________________________
**Prerequisites**
•	Flutter SDK installed
•	Android Studio or VS Code
•	Android device or emulator
•	Python (for backend if used)


**Demo Link**
https://drive.google.com/file/d/12nXlg5Lchd4kJht1HJMkEp3eiNe9P8tt/view?usp=drivesdk

**Team Roles**
Names	                      Roles
Snehal B Rai	    |   ML Engineer-Model Development            |
Kashish           |  	ML Engineer-ML Engineer                  |
Chandu Shree S	  |   ML Engineer- Data Engineer and Researcher|
Dikshitha Ramesh  |   Frontend Developer                       |
Lasya T P         |  	Backend Developer                        |
Nithin N Pate     |   Research and App Developer               |
Tejas V           |	  Backend Developer                        |
Savari Yevoor     |   Integration Developer                    |
Pooja	            |   Integration Developer                    |
Narayan M Nayak   |  	Mobile App Developer                     |
B V Vedamurthi	  |   Mobile App Developer                     |
Priyaguna	        |   Testing-QA Tester                        |
Tamirah Sharieff 	|   Testing-User Testing and Accessibility   |
Ammar Shibli	    |   Reasearch Analyst                        |
Manisha M S     	|   Documentation and Frontend Developer     |

