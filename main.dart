import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_tts/flutter_tts.dart';
import 'dart:async';

List<CameraDescription>? cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  cameras = await availableCameras();
  runApp(const SafeStrideApp());
}

// ─── LOCALIZATION ──────────────────────────────────────────────────────────────
enum AppLanguage { english, kannada }

class AppStrings {
  final AppLanguage language;
  const AppStrings(this.language);
  bool get isKannada => language == AppLanguage.kannada;

  String get appName        => isKannada ? 'ಸೇಫ್‌ಸ್ಟ್ರೈಡ್' : 'SafeStride';
  String get tagline        => isKannada ? 'ಎಐ ಶಕ್ತಿಯ ದೃಷ್ಟಿ, ಪ್ರತಿ ಹೆಜ್ಜೆ ಸಂರಕ್ಷಿಸುತ್ತದೆ' : 'AI-Powered Vision, Protecting Every Step';
  String get homeSubtitle   => isKannada ? 'ದೃಷ್ಟಿ ಮಿತಿ ಹೊಂದಿರುವವರಿಗೆ ರಿಯಲ್-ಟೈಮ್ ಅಡಚಣೆ ಪತ್ತೆ' : 'Real-time obstacle detection for the visually impaired';
  String get startButton    => isKannada ? 'ಸ್ಕ್ಯಾನಿಂಗ್ ಪ್ರಾರಂಭಿಸಿ' : 'Start Scanning';
  String get howItWorks     => isKannada ? 'ಹೇಗೆ ಕಾರ್ಯ ನಿರ್ವಹಿಸುತ್ತದೆ' : 'How It Works';
  String get feature1Title  => isKannada ? 'ತ್ವರಿತ ಪತ್ತೆ' : 'Instant Detection';
  String get feature1Desc   => isKannada ? 'ರಿಯಲ್-ಟೈಮ್ ಅಡಚಣೆ ಗುರುತಿಸುವಿಕೆ' : 'Real-time obstacle recognition';
  String get feature2Title  => isKannada ? 'ಧ್ವನಿ ಎಚ್ಚರಿಕೆ' : 'Voice Alerts';
  String get feature2Desc   => isKannada ? 'ಸ್ಪಷ್ಟ ಶ್ರವ್ಯ ಸೂಚನೆಗಳು' : 'Clear audible guidance';
  String get feature3Title  => isKannada ? 'ದಿಕ್ಕು ಮಾರ್ಗದರ್ಶನ' : 'Direction Guidance';
  String get feature3Desc   => isKannada ? 'ನಿಖರ ದಿಕ್ಕು ಮತ್ತು ದೂರ ಮಾಹಿತಿ' : 'Precise direction & distance info';
  String get liveLabel      => isKannada ? 'ಲೈವ್' : 'LIVE';
  String get pausedLabel    => isKannada ? 'ನಿಲ್ಲಿಸಲಾಗಿದೆ' : 'PAUSED';
  String get tapToStart     => isKannada ? 'ಪ್ರಾರಂಭಿಸಲು ಮೈಕ್ ಒತ್ತಿ' : 'Tap the mic button to start';
  String get scanning       => isKannada ? 'ಸ್ಕ್ಯಾನ್ ಮಾಡಲಾಗುತ್ತಿದೆ…' : 'Scanning…';
  String get clearPath      => isKannada ? 'ಮಾರ್ಗ ಸ್ಪಷ್ಟವಾಗಿದೆ' : 'Clear path';
  String get detectionPaused => isKannada ? 'ಪತ್ತೆ ನಿಲ್ಲಿಸಲಾಗಿದೆ' : 'Detection paused';
  String get connError      => isKannada ? 'ಸಂಪರ್ಕ ದೋಷ' : 'Connection error';
  String get aiReady        => isKannada ? 'ಎಐ ಮಾದರಿ ಸಿದ್ಧ' : 'AI Model Ready';
  String get step1Title     => isKannada ? 'ಕ್ಯಾಮೆರಾ ತೆರೆಯಿರಿ' : 'Open Camera';
  String get step1Desc      => isKannada ? 'ಸ್ಕ್ಯಾನ್ ಪ್ರಾರಂಭಿಸಲು ಸ್ಟಾರ್ಟ್ ಒತ್ತಿ' : 'Press start to begin scanning your environment';
  String get step2Title     => isKannada ? 'ಎಐ ವಿಶ್ಲೇಷಣೆ' : 'AI Analysis';
  String get step2Desc      => isKannada ? 'ಮಾದರಿಯು ರಿಯಲ್-ಟೈಮ್ ಚಿತ್ರ ಪ್ರಕ್ರಿಯೆ ಮಾಡುತ್ತದೆ' : 'The model processes frames in real-time';
  String get step3Title     => isKannada ? 'ಧ್ವನಿ ಮಾರ್ಗದರ್ಶನ' : 'Voice Guidance';
  String get step3Desc      => isKannada ? 'ಅಡಚಣೆ ಮತ್ತು ದಿಕ್ಕಿನ ಶ್ರವ್ಯ ಎಚ್ಚರಿಕೆ ಪಡೆಯಿರಿ' : 'Receive audible alerts for obstacles & direction';
}

// ─── LANGUAGE NOTIFIER ────────────────────────────────────────────────────────
class LanguageNotifier extends ChangeNotifier {
  AppLanguage _lang = AppLanguage.english;
  AppLanguage get language => _lang;
  AppStrings get strings => AppStrings(_lang);
  void toggle() {
    _lang = _lang == AppLanguage.english ? AppLanguage.kannada : AppLanguage.english;
    notifyListeners();
  }
}

// ─── ROOT APP ─────────────────────────────────────────────────────────────────
class SafeStrideApp extends StatefulWidget {
  const SafeStrideApp({super.key});
  @override
  State<SafeStrideApp> createState() => _SafeStrideAppState();
}

class _SafeStrideAppState extends State<SafeStrideApp> {
  final LanguageNotifier _langNotifier = LanguageNotifier();
  @override
  void dispose() { _langNotifier.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _langNotifier,
      builder: (context, _) => MaterialApp(
        title: 'SafeStride',
        debugShowCheckedModeBanner: false,
        theme: ThemeData.dark().copyWith(
          scaffoldBackgroundColor: const Color(0xFF080C12),
          colorScheme: const ColorScheme.dark(
            primary: Color(0xFF00E5C3),
            secondary: Color(0xFF0A9ED9),
            surface: Color(0xFF0F1720),
          ),
        ),
        home: HomePage(langNotifier: _langNotifier),
      ),
    );
  }
}

// ─── HOME PAGE ────────────────────────────────────────────────────────────────
class HomePage extends StatefulWidget {
  final LanguageNotifier langNotifier;
  const HomePage({super.key, required this.langNotifier});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> with TickerProviderStateMixin {
  late final AnimationController _fadeCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))..forward();
  late final AnimationController _floatCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 3))..repeat(reverse: true);
  late final AnimationController _pulseCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat(reverse: true);
  late final Animation<double> _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
  late final Animation<double> _floatAnim = Tween<double>(begin: -8, end: 8).animate(CurvedAnimation(parent: _floatCtrl, curve: Curves.easeInOut));
  late final Animation<double> _pulseAnim = Tween<double>(begin: 0.7, end: 1.0).animate(_pulseCtrl);

  @override
  void dispose() { _fadeCtrl.dispose(); _floatCtrl.dispose(); _pulseCtrl.dispose(); super.dispose(); }

  AppStrings get s => widget.langNotifier.strings;

  void _goToScanner() => Navigator.of(context).push(
    PageRouteBuilder(
      pageBuilder: (_, anim, __) => SafeStridePage(langNotifier: widget.langNotifier),
      transitionsBuilder: (_, anim, __, child) => FadeTransition(opacity: anim, child: child),
      transitionDuration: const Duration(milliseconds: 500),
    ),
  );

  void _showHowItWorks() => showModalBottomSheet(
    context: context,
    backgroundColor: const Color(0xFF0F1720),
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
    builder: (_) => _HowItWorksSheet(langNotifier: widget.langNotifier),
  );

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    return Scaffold(
      backgroundColor: const Color(0xFF080C12),
      body: Stack(
        children: [
          // Ambient glows
          Positioned(top: -size.height * 0.12, right: -size.width * 0.2,
            child: _GlowOrb(color: const Color(0xFF00E5C3), size: size.width * 0.7, opacity: 0.07)),
          Positioned(bottom: -size.height * 0.05, left: -size.width * 0.25,
            child: _GlowOrb(color: const Color(0xFF0A9ED9), size: size.width * 0.8, opacity: 0.06)),
          Positioned(top: size.height * 0.45, left: size.width * 0.3,
            child: _GlowOrb(color: const Color(0xFF00E5C3), size: size.width * 0.3, opacity: 0.04)),
          // Grid
          Positioned.fill(child: CustomPaint(painter: _GridPainter())),

          // Main scrollable content
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 28),
              child: FadeTransition(
                opacity: _fadeAnim,
                child: ListenableBuilder(
                  listenable: widget.langNotifier,
                  builder: (_, __) => Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const SizedBox(height: 20),

                      // Top bar
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(children: [
                            Container(
                              width: 38, height: 38,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: const Color(0xFF00E5C3).withOpacity(0.12),
                                border: Border.all(color: const Color(0xFF00E5C3), width: 1.5),
                              ),
                              child: const Icon(Icons.accessibility_new, color: Color(0xFF00E5C3), size: 20),
                            ),
                            const SizedBox(width: 10),
                            Text(s.appName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Colors.white, letterSpacing: 1.2)),
                          ]),
                          _LanguageToggle(notifier: widget.langNotifier),
                        ],
                      ),

                      const SizedBox(height: 56),

                      // Floating hero icon
                      AnimatedBuilder(
                        animation: _floatAnim,
                        builder: (_, child) => Transform.translate(offset: Offset(0, _floatAnim.value), child: child),
                        child: AnimatedBuilder(
                          animation: _pulseAnim,
                          builder: (_, child) => Container(
                            width: 150, height: 150,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: const Color(0xFF0F1720),
                              border: Border.all(color: const Color(0xFF00E5C3).withOpacity(_pulseAnim.value), width: 2),
                              boxShadow: [BoxShadow(
                                color: const Color(0xFF00E5C3).withOpacity(0.22 * _pulseAnim.value),
                                blurRadius: 50, spreadRadius: 12,
                              )],
                            ),
                            child: Stack(alignment: Alignment.center, children: [
                              Container(width: 115, height: 115, decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(color: const Color(0xFF00E5C3).withOpacity(0.2), width: 1),
                              )),
                              const Icon(Icons.remove_red_eye_outlined, color: Color(0xFF00E5C3), size: 56),
                            ]),
                          ),
                        ),
                      ),

                      const SizedBox(height: 40),

                      // Headline
                      Text(s.appName, style: const TextStyle(fontSize: 44, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2, height: 1.1), textAlign: TextAlign.center),
                      const SizedBox(height: 14),
                      ShaderMask(
                        shaderCallback: (bounds) => const LinearGradient(colors: [Color(0xFF00E5C3), Color(0xFF0A9ED9)]).createShader(bounds),
                        child: Text(s.tagline, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white, height: 1.4), textAlign: TextAlign.center),
                      ),
                      const SizedBox(height: 10),
                      Text(s.homeSubtitle, style: const TextStyle(fontSize: 13, color: Colors.white38, height: 1.5), textAlign: TextAlign.center),

                      const SizedBox(height: 44),

                      // Feature cards
                      Row(children: [
                        Expanded(child: _FeatureCard(icon: Icons.bolt, title: s.feature1Title, desc: s.feature1Desc)),
                        const SizedBox(width: 10),
                        Expanded(child: _FeatureCard(icon: Icons.volume_up_outlined, title: s.feature2Title, desc: s.feature2Desc)),
                        const SizedBox(width: 10),
                        Expanded(child: _FeatureCard(icon: Icons.explore_outlined, title: s.feature3Title, desc: s.feature3Desc)),
                      ]),

                      const SizedBox(height: 44),

                      // CTA
                      _StartButton(label: s.startButton, onTap: _goToScanner),
                      const SizedBox(height: 16),

                      TextButton(
                        onPressed: _showHowItWorks,
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          Text(s.howItWorks, style: const TextStyle(color: Colors.white38, fontSize: 13, letterSpacing: 0.5)),
                          const SizedBox(width: 4),
                          const Icon(Icons.arrow_forward_ios, color: Colors.white24, size: 11),
                        ]),
                      ),

                      const SizedBox(height: 28),

                      // Status bar
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F1720).withOpacity(0.6),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.white.withOpacity(0.06)),
                        ),
                        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          Container(width: 7, height: 7, decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF00E5C3))),
                          const SizedBox(width: 8),
                          Text(s.aiReady, style: const TextStyle(color: Colors.white38, fontSize: 12, letterSpacing: 1)),
                        ]),
                      ),

                      const SizedBox(height: 32),
                    ],
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

// ─── LANGUAGE TOGGLE ──────────────────────────────────────────────────────────
class _LanguageToggle extends StatelessWidget {
  final LanguageNotifier notifier;
  const _LanguageToggle({required this.notifier});

  @override
  Widget build(BuildContext context) {
    final isKannada = notifier.language == AppLanguage.kannada;
    return GestureDetector(
      onTap: notifier.toggle,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: const Color(0xFF0F1720),
          borderRadius: BorderRadius.circular(30),
          border: Border.all(color: const Color(0xFF00E5C3).withOpacity(0.4), width: 1.2),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          _LangChip(label: 'EN', active: !isKannada),
          const SizedBox(width: 2),
          _LangChip(label: 'ಕನ್ನಡ', active: isKannada),
        ]),
      ),
    );
  }
}

class _LangChip extends StatelessWidget {
  final String label;
  final bool active;
  const _LangChip({required this.label, required this.active});

  @override
  Widget build(BuildContext context) => AnimatedContainer(
    duration: const Duration(milliseconds: 250),
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: active ? const Color(0xFF00E5C3) : Colors.transparent,
      borderRadius: BorderRadius.circular(24),
    ),
    child: Text(label, style: TextStyle(
      fontSize: 11, fontWeight: FontWeight.w700,
      color: active ? const Color(0xFF080C12) : Colors.white38,
      letterSpacing: 0.5,
    )),
  );
}

// ─── FEATURE CARD ─────────────────────────────────────────────────────────────
class _FeatureCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String desc;
  const _FeatureCard({required this.icon, required this.title, required this.desc});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: const Color(0xFF0F1720).withOpacity(0.8),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: const Color(0xFF00E5C3).withOpacity(0.15)),
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Container(
        width: 36, height: 36,
        decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFF00E5C3).withOpacity(0.12)),
        child: Icon(icon, color: const Color(0xFF00E5C3), size: 18),
      ),
      const SizedBox(height: 10),
      Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Colors.white, height: 1.3)),
      const SizedBox(height: 4),
      Text(desc, style: const TextStyle(fontSize: 10, color: Colors.white38, height: 1.4)),
    ]),
  );
}

// ─── START BUTTON ─────────────────────────────────────────────────────────────
class _StartButton extends StatefulWidget {
  final String label;
  final VoidCallback onTap;
  const _StartButton({required this.label, required this.onTap});
  @override
  State<_StartButton> createState() => _StartButtonState();
}

class _StartButtonState extends State<_StartButton> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 120));
  late final Animation<double> _scale = Tween<double>(begin: 1, end: 0.96).animate(_ctrl);
  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTapDown: (_) => _ctrl.forward(),
    onTapUp: (_) { _ctrl.reverse(); widget.onTap(); },
    onTapCancel: () => _ctrl.reverse(),
    child: AnimatedBuilder(
      animation: _scale,
      builder: (_, child) => Transform.scale(scale: _scale.value, child: child),
      child: Container(
        width: double.infinity, height: 60,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30),
          gradient: const LinearGradient(colors: [Color(0xFF00E5C3), Color(0xFF0A9ED9)], begin: Alignment.centerLeft, end: Alignment.centerRight),
          boxShadow: [BoxShadow(color: const Color(0xFF00E5C3).withOpacity(0.35), blurRadius: 20, spreadRadius: 2, offset: const Offset(0, 4))],
        ),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.play_circle_outline, color: Color(0xFF080C12), size: 22),
          const SizedBox(width: 10),
          Text(widget.label, style: const TextStyle(color: Color(0xFF080C12), fontSize: 16, fontWeight: FontWeight.w800, letterSpacing: 0.5)),
        ]),
      ),
    ),
  );
}

// ─── HOW IT WORKS SHEET ───────────────────────────────────────────────────────
class _HowItWorksSheet extends StatelessWidget {
  final LanguageNotifier langNotifier;
  const _HowItWorksSheet({required this.langNotifier});

  @override
  Widget build(BuildContext context) {
    final s = langNotifier.strings;
    final steps = [
      (Icons.camera_alt_outlined, s.step1Title, s.step1Desc),
      (Icons.psychology_outlined, s.step2Title, s.step2Desc),
      (Icons.record_voice_over_outlined, s.step3Title, s.step3Desc),
    ];
    return Padding(
      padding: const EdgeInsets.all(28),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white12, borderRadius: BorderRadius.circular(2)))),
        const SizedBox(height: 24),
        Text(s.howItWorks, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800, letterSpacing: 0.5)),
        const SizedBox(height: 24),
        ...steps.map((step) => Padding(
          padding: const EdgeInsets.only(bottom: 18),
          child: Row(children: [
            Container(
              width: 40, height: 40,
              decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFF00E5C3).withOpacity(0.12), border: Border.all(color: const Color(0xFF00E5C3).withOpacity(0.3))),
              child: Icon(step.$1, color: const Color(0xFF00E5C3), size: 20),
            ),
            const SizedBox(width: 16),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(step.$2, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14)),
              const SizedBox(height: 2),
              Text(step.$3, style: const TextStyle(color: Colors.white38, fontSize: 12)),
            ])),
          ]),
        )),
        const SizedBox(height: 8),
      ]),
    );
  }
}

// ─── AMBIENT GLOW ─────────────────────────────────────────────────────────────
class _GlowOrb extends StatelessWidget {
  final Color color; final double size, opacity;
  const _GlowOrb({required this.color, required this.size, required this.opacity});

  @override
  Widget build(BuildContext context) => Container(
    width: size, height: size,
    decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [color.withOpacity(opacity), Colors.transparent])),
  );
}

// ─── GRID PAINTER ─────────────────────────────────────────────────────────────
class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = const Color(0xFF00E5C3).withOpacity(0.025)..strokeWidth = 0.5;
    for (double x = 0; x < size.width; x += 40) canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    for (double y = 0; y < size.height; y += 40) canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
  }
  @override
  bool shouldRepaint(_) => false;
}

// ─── DETECTION MODEL ──────────────────────────────────────────────────────────
class Detection {
  final String label, direction, proximity, alertText;
  final double confidence;
  final Map<String, int> bbox;

  const Detection({required this.label, required this.confidence, required this.direction, required this.proximity, required this.alertText, required this.bbox});

  factory Detection.fromJson(Map<String, dynamic> j) => Detection(
    label: j['label'] as String, confidence: (j['confidence'] as num).toDouble(),
    direction: j['direction'] as String, proximity: j['proximity'] as String,
    alertText: j['alert_text'] as String,
    bbox: Map<String, int>.from((j['bbox'] as Map).map((k, v) => MapEntry(k as String, v as int))),
  );

  String get proximityBadge => proximity == 'very close' ? '🔴' : proximity == 'close' ? '🟡' : '🟢';
}

// ─── SCANNER PAGE ─────────────────────────────────────────────────────────────
class SafeStridePage extends StatefulWidget {
  final LanguageNotifier langNotifier;
  const SafeStridePage({super.key, required this.langNotifier});
  @override
  State<SafeStridePage> createState() => _SafeStridePageState();
}

class _SafeStridePageState extends State<SafeStridePage> with TickerProviderStateMixin {
  CameraController? _cameraController;
  bool _cameraReady = false;
  bool _isProcessing = false;
  bool _isDetecting = false;
  Timer? _inferenceTimer;
  List<Detection> _detections = [];
  int _imageWidth = 640, _imageHeight = 480;
  String _statusKey = 'tapToStart';

  late final AnimationController _pulseCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..repeat(reverse: true);
  late final Animation<double> _pulseAnim = Tween<double>(begin: 0.4, end: 1.0).animate(_pulseCtrl);

  final FlutterTts _tts = FlutterTts();
  static const String _apiUrl = 'http://localhost:8000/detect';
  static const int _frameIntervalMs = 1200;

  AppStrings get s => widget.langNotifier.strings;

  String get _statusText {
    switch (_statusKey) {
      case 'tapToStart': return s.tapToStart;
      case 'scanning':   return s.scanning;
      case 'clearPath':  return s.clearPath;
      case 'paused':     return s.detectionPaused;
      case 'connError':  return s.connError;
      default:           return _statusKey;
    }
  }

  @override
  void initState() {
    super.initState();
    _initTts();
    _initCamera();
    widget.langNotifier.addListener(_onLangChange);
  }

  void _onLangChange() { _updateTtsLanguage(); if (mounted) setState(() {}); }

  Future<void> _initTts() async { await _updateTtsLanguage(); await _tts.setSpeechRate(0.50); await _tts.setVolume(1.0); }

  Future<void> _updateTtsLanguage() async {
    await _tts.setLanguage(widget.langNotifier.language == AppLanguage.kannada ? 'kn-IN' : 'en-US');
  }

  Future<void> _initCamera() async {
    if (cameras == null || cameras!.isEmpty) return;
    _cameraController = CameraController(cameras![0], ResolutionPreset.medium, enableAudio: false);
    await _cameraController!.initialize();
    if (mounted) setState(() { _cameraReady = true; _isDetecting = true; _statusKey = 'scanning'; });
    _startInferenceLoop();
  }

  void _startInferenceLoop() {
    _inferenceTimer?.cancel();
    _inferenceTimer = Timer.periodic(const Duration(milliseconds: _frameIntervalMs), (_) => _captureAndProcess());
  }

  void _stopInferenceLoop() { _inferenceTimer?.cancel(); _inferenceTimer = null; }

  Future<void> _captureAndProcess() async {
    if (!_isDetecting || _isProcessing || !_cameraReady) return;
    try {
      _isProcessing = true;
      final XFile file = await _cameraController!.takePicture();
      final Uint8List bytes = await file.readAsBytes();
      await _processFrame(bytes);
    } catch (e) { debugPrint('Capture error: $e'); } finally { _isProcessing = false; }
  }

  Future<void> _processFrame(Uint8List bytes) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse(_apiUrl));
      request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: 'frame.jpg'));
      final streamed = await request.send().timeout(const Duration(seconds: 5));
      if (streamed.statusCode == 200) {
        final body = await streamed.stream.bytesToString();
        final json = jsonDecode(body) as Map<String, dynamic>;
        final detections = (json['results'] as List<dynamic>).map((e) => Detection.fromJson(e as Map<String, dynamic>)).toList();
        if (detections.isNotEmpty) await _tts.speak(detections.map((d) => d.alertText).toSet().join('. '));
        if (mounted) setState(() { _detections = detections; _imageWidth = json['width'] ?? _imageWidth; _imageHeight = json['height'] ?? _imageHeight; _statusKey = detections.isEmpty ? 'clearPath' : ''; });
      } else if (mounted) setState(() => _statusKey = 'connError');
    } catch (e) { if (mounted) setState(() => _statusKey = 'connError'); } finally { _isProcessing = false; }
  }

  void _toggleDetection() {
    setState(() {
      _isDetecting = !_isDetecting;
      if (!_isDetecting) { _stopInferenceLoop(); _detections = []; _statusKey = 'paused'; _tts.stop(); }
      else { _statusKey = 'scanning'; _startInferenceLoop(); }
    });
  }

  @override
  void dispose() {
    widget.langNotifier.removeListener(_onLangChange);
    _pulseCtrl.dispose(); _stopInferenceLoop(); _cameraController?.dispose(); _tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: widget.langNotifier,
    builder: (context, _) => Scaffold(
      backgroundColor: const Color(0xFF080C12),
      body: Stack(children: [
        // Camera
        if (_cameraReady)
          Positioned.fill(child: LayoutBuilder(builder: (context, constraints) => Stack(children: [
            Positioned.fill(child: CameraPreview(_cameraController!)),
            Positioned.fill(child: CustomPaint(painter: BoundingBoxPainter(detections: _detections, imageWidth: _imageWidth, imageHeight: _imageHeight, screenWidth: constraints.maxWidth, screenHeight: constraints.maxHeight))),
          ])))
        else
          const Positioned.fill(child: Center(child: CircularProgressIndicator(color: Color(0xFF00E5C3)))),

        // Gradient overlay
        Positioned.fill(child: DecoratedBox(decoration: BoxDecoration(gradient: LinearGradient(
          begin: Alignment.topCenter, end: Alignment.bottomCenter,
          colors: [const Color(0xFF080C12).withOpacity(0.65), Colors.transparent, Colors.transparent, const Color(0xFF080C12).withOpacity(0.92)],
          stops: const [0, 0.18, 0.55, 1],
        )))),

        // Top bar
        Positioned(top: 0, left: 0, right: 0, child: SafeArea(child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          child: Row(children: [
            GestureDetector(
              onTap: () => Navigator.of(context).pop(),
              child: Container(
                width: 36, height: 36,
                decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.black.withOpacity(0.4), border: Border.all(color: Colors.white12)),
                child: const Icon(Icons.arrow_back_ios_new, color: Colors.white54, size: 16),
              ),
            ),
            const SizedBox(width: 12),
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(shape: BoxShape.circle, color: const Color(0xFF00E5C3).withOpacity(0.15), border: Border.all(color: const Color(0xFF00E5C3), width: 1.5)),
              child: const Icon(Icons.accessibility_new, color: Color(0xFF00E5C3), size: 16),
            ),
            const SizedBox(width: 8),
            Text(s.appName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colors.white, letterSpacing: 1.2)),
            const Spacer(),
            _LanguageToggle(notifier: widget.langNotifier),
            const SizedBox(width: 12),
            if (_isDetecting)
              AnimatedBuilder(
                animation: _pulseAnim,
                builder: (_, __) => Opacity(opacity: _pulseAnim.value, child: Row(children: [
                  Container(width: 8, height: 8, decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF00E5C3))),
                  const SizedBox(width: 6),
                  Text(s.liveLabel, style: const TextStyle(color: Color(0xFF00E5C3), fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 2)),
                ])),
              )
            else
              Text(s.pausedLabel, style: const TextStyle(color: Colors.white38, fontSize: 12, letterSpacing: 2)),
          ]),
        ))),

        // Detection cards
        Positioned(bottom: 120, left: 16, right: 16, child: Column(mainAxisSize: MainAxisSize.min, children: [
          if (_detections.isEmpty) _StatusChip(text: _statusText)
          else ..._detections.take(4).map((d) => _DetectionCard(d)),
        ])),

        // Toggle button
        Positioned(bottom: 36, left: 0, right: 0, child: Center(child: GestureDetector(
          onTap: _toggleDetection,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 72, height: 72,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _isDetecting ? const Color(0xFFE53935) : const Color(0xFF00E5C3),
              boxShadow: [BoxShadow(color: (_isDetecting ? const Color(0xFFE53935) : const Color(0xFF00E5C3)).withOpacity(0.45), blurRadius: 24, spreadRadius: 4)],
            ),
            child: Icon(_isDetecting ? Icons.mic_off : Icons.mic, color: Colors.white, size: 30),
          ),
        ))),
      ]),
    ),
  );
}

// ─── WIDGETS ──────────────────────────────────────────────────────────────────
class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) {
    if (text.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
      decoration: BoxDecoration(color: const Color(0xFF0F1720).withOpacity(0.85), borderRadius: BorderRadius.circular(30), border: Border.all(color: Colors.white12)),
      child: Text(text, style: const TextStyle(color: Colors.white60, fontSize: 14, letterSpacing: 0.5)),
    );
  }
}

class _DetectionCard extends StatelessWidget {
  const _DetectionCard(this.d);
  final Detection d;
  @override
  Widget build(BuildContext context) {
    final Color accent = d.proximity == 'very close' ? const Color(0xFFE53935) : d.proximity == 'close' ? const Color(0xFFFFAB00) : const Color(0xFF00E5C3);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(color: const Color(0xFF0F1720).withOpacity(0.88), borderRadius: BorderRadius.circular(14), border: Border.all(color: accent.withOpacity(0.55), width: 1.2)),
      child: Row(children: [
        Text(d.proximityBadge, style: const TextStyle(fontSize: 20)),
        const SizedBox(width: 12),
        Expanded(child: Text(d.alertText, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500))),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(color: accent.withOpacity(0.15), borderRadius: BorderRadius.circular(20), border: Border.all(color: accent.withOpacity(0.4))),
          child: Text('${(d.confidence * 100).round()}%', style: TextStyle(color: accent, fontSize: 11, fontWeight: FontWeight.w700)),
        ),
      ]),
    );
  }
}

// ─── BOUNDING BOX PAINTER ─────────────────────────────────────────────────────
class BoundingBoxPainter extends CustomPainter {
  final List<Detection> detections;
  final int imageWidth, imageHeight;
  final double screenWidth, screenHeight;

  BoundingBoxPainter({required this.detections, required this.imageWidth, required this.imageHeight, required this.screenWidth, required this.screenHeight});

  @override
  void paint(Canvas canvas, Size size) {
    if (detections.isEmpty) return;
    final scaleX = screenWidth / imageWidth, scaleY = screenHeight / imageHeight;
    for (var d in detections) {
      if (!d.bbox.containsKey('x1')) continue;
      final rect = Rect.fromLTRB(d.bbox['x1']! * scaleX, d.bbox['y1']! * scaleY, d.bbox['x2']! * scaleX, d.bbox['y2']! * scaleY);
      final paint = Paint()..style = PaintingStyle.stroke..strokeWidth = 3.0..color = d.proximity == 'very close' ? const Color(0xFFE53935) : d.proximity == 'close' ? const Color(0xFFFFAB00) : const Color(0xFF00E5C3);
      canvas.drawRRect(RRect.fromRectAndRadius(rect, const Radius.circular(8)), paint);
      final tp = TextPainter(
        text: TextSpan(text: '${d.label} ${(d.confidence * 100).round()}%', style: TextStyle(color: Colors.black87, backgroundColor: paint.color, fontSize: 14, fontWeight: FontWeight.bold)),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(rect.left, rect.top - tp.height));
    }
  }

  @override
  bool shouldRepaint(covariant BoundingBoxPainter _) => true;
}
