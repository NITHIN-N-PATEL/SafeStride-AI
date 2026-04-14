import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_tts/flutter_tts.dart';

List<CameraDescription>? cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  cameras = await availableCameras();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: CameraPage(),
    );
  }
}

class CameraPage extends StatefulWidget {
  const CameraPage({super.key});

  @override
  State<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends State<CameraPage> {
  CameraController? controller;

  bool isProcessing = false;
  bool isDetecting = true;

  String result = "Initializing...";
  DateTime lastFrameTime = DateTime.now();

  final FlutterTts tts = FlutterTts();

  final String apiUrl = "http://192.168.1.5:8000/detect"; // 🔥 CHANGE THIS

  @override
  void initState() {
    super.initState();
    initCamera();
    tts.setSpeechRate(0.5);
  }

  Future<void> initCamera() async {
    controller = CameraController(
      cameras![0],
      ResolutionPreset.medium,
      enableAudio: false,
    );

    await controller!.initialize();

    controller!.startImageStream((CameraImage image) {
      if (!isProcessing &&
          isDetecting &&
          DateTime.now().difference(lastFrameTime).inMilliseconds > 1200) {
        lastFrameTime = DateTime.now();
        isProcessing = true;
        processFrame(image);
      }
    });

    setState(() {});
  }

  Future<void> processFrame(CameraImage image) async {
    try {
      Uint8List bytes = image.planes[0].bytes;

      var request = http.MultipartRequest(
        "POST",
        Uri.parse(apiUrl),
      );

      request.files.add(
        http.MultipartFile.fromBytes("file", bytes, filename: "frame.jpg"),
      );

      var response = await request.send();

      if (response.statusCode == 200) {
        var res = json.decode(await response.stream.bytesToString());
        List detections = res["results"];

        if (detections.isEmpty) {
          setState(() => result = "No objects detected");
        } else {
          String text = "";
          bool danger = false;

          for (var obj in detections) {
            text += obj["label"] + ", ";

            if (obj["label"].toLowerCase() == "pothole" ||
                obj["label"].toLowerCase() == "manhole") {
              danger = true;
            }
          }

          setState(() => result = text);

          await tts.speak(
            danger ? "Warning! $text" : text,
          );
        }
      } else {
        result = "Server error";
      }
    } catch (e) {
      result = "Error";
    }

    isProcessing = false;
  }

  void toggleDetection() {
    setState(() {
      isDetecting = !isDetecting;
      result = isDetecting ? "Resumed" : "Paused";
    });
  }

  @override
  void dispose() {
    controller?.dispose();
    tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (controller == null || !controller!.value.isInitialized) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      body: Stack(
        children: [
          // 📷 Camera
          Positioned.fill(
            child: CameraPreview(controller!),
          ),

          // 🔝 Top Bar
          Positioned(
            top: 40,
            left: 20,
            right: 20,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.4),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    "Vision Assist",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Row(
                    children: [
                      Icon(
                        Icons.circle,
                        color: isDetecting ? Colors.green : Colors.red,
                        size: 12,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        isDetecting ? "LIVE" : "PAUSED",
                        style: const TextStyle(color: Colors.white),
                      ),
                    ],
                  )
                ],
              ),
            ),
          ),

          // 📊 Result Card
          Positioned(
            bottom: 120,
            left: 20,
            right: 20,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.5),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    "Detected Objects",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    result,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.greenAccent,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // 🔘 Floating Button
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Center(
              child: GestureDetector(
                onTap: toggleDetection,
                child: Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isDetecting ? Colors.red : Colors.green,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.4),
                        blurRadius: 10,
                      )
                    ],
                  ),
                  child: Icon(
                    isDetecting ? Icons.stop : Icons.play_arrow,
                    color: Colors.white,
                    size: 30,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}