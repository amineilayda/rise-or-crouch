import 'dart:math';

import 'package:flame_3d/camera.dart';
import 'package:flame_3d/core.dart';

enum CameraMode { menu, intro, firstPerson, loseView }

/// Oyunun kamerası.
///
/// - Menüde yukarıda, sahneye tepeden bakar.
/// - Oyun başlayınca ([startIntro]): sıranın arkasına iner, oyuncunun kafasına
///   girip birinci şahısa geçer, sola ve sağa bakıp oyun kurucuya döner.
/// - Birinci şahısta oyuncu çömelince göz hizası alçalır.
/// - Yanınca ([showLoseView]) geri çekilip oyuncuyu arkadan gösterir.
class StageCamera extends CameraComponent3D {
  StageCamera({required this.playerX, required this.lookAt})
    : super(fovY: 70, position: Vector3(0, 9, 15), target: lookAt);

  final double playerX;

  /// Oyun kurucunun yüzü; birinci şahısta bakılan nokta.
  final Vector3 lookAt;

  // Birinci şahıs göz yüksekliği (Mage'in gözleri) ve çömelince.
  static const double standEyeY = 1.3;
  static const double crouchEyeY = 0.95;

  // Giriş zaman çizelgesi (saniye).
  static const double _toBehindEnd = 2.2;
  static const double _toEyeEnd = 3.2;
  static const double _lookStart = 3.4;
  static const double _lookEnd = 5.8;
  static const double introDuration = _lookEnd;

  /// Sola/sağa bakarken dönülen açı (derece).
  static const double _lookAngle = 65;

  final Vector3 _menuPosition = Vector3(0, 9, 15);
  late final Vector3 _behindPosition = Vector3(playerX, 2.6, 3.2);
  late final Vector3 _losePosition = Vector3(playerX + 1.2, 2.4, 3.4);
  late final Vector3 _loseTarget = Vector3(playerX, 0.7, 0);

  CameraMode _mode = CameraMode.menu;
  double _time = 0;
  double _eyeY = standEyeY;
  bool crouched = false;

  final Vector3 _blendFromPosition = Vector3.zero();
  final Vector3 _blendFromTarget = Vector3.zero();

  final Random _random = Random();
  double _shakeStrength = 0;
  double _shakeDuration = 0;
  double _shakeTime = 0;

  /// Birinci şahısta bakılan hedef (ör. yanan oyuncu) ve ne zamana kadar.
  Vector3 Function()? _glanceTarget;
  bool Function()? _glanceUntil;
  double _glanceTime = 0;
  double? _glanceReturnAt;
  static const double _glanceMax = 10;
  static const double _glanceTurn = 0.4;
  static const double _glanceReturn = 0.5;

  /// Yana bakarken kamera kafanın içinden sıranın arkasına ve biraz yukarı
  /// çekilir: yanımızdakiler bu kadar yakından ekrana sığmıyor.
  static final Vector3 _sideViewOffset = Vector3(0, 0.7, 2.4);

  /// Şu anki geri çekilme oranı (0 kafanın içi, 1 tam geride).
  double _pullBack = 0;

  /// Kamera bir şeye bakıyor mu (o sırada oyun duraklar).
  bool get isGlancing => _glanceTarget != null;

  /// Birinci şahısta başı [target]'a çevirir, [until] doğru olana kadar takip
  /// eder ve geri döner. [target] her karede yeniden okunur; yürüyen birini izler.
  void glanceAt(Vector3 Function() target, {required bool Function() until}) {
    _glanceTarget = target;
    _glanceUntil = until;
    _glanceTime = 0;
    _glanceReturnAt = null;
  }

  bool get introFinished => _mode == CameraMode.firstPerson;

  /// Kamera oyuncunun kafasının içinde mi? (O zaman oyuncu modeli gizlenmeli.)
  /// Yana bakmak için geri çekilince oyuncu yeniden görünür.
  bool get insideHead =>
      _pullBack < 0.35 &&
      (_mode == CameraMode.firstPerson ||
          (_mode == CameraMode.intro &&
              _time > _toBehindEnd + (_toEyeEnd - _toBehindEnd) * 0.75));

  void showMenuView() => _setMode(CameraMode.menu);

  void startIntro() {
    crouched = false;
    _eyeY = standEyeY;
    _setMode(CameraMode.intro);
  }

  void showLoseView() => _setMode(CameraMode.loseView);

  /// Kısa süreli kamera sarsıntısı (ör. yanınca). [strength] metre cinsinden.
  void shake({double strength = 0.25, double duration = 0.45}) {
    _shakeStrength = strength;
    _shakeDuration = duration;
    _shakeTime = 0;
  }

  void _setMode(CameraMode mode) {
    _mode = mode;
    _time = 0;
    _glanceTarget = null;
    _glanceUntil = null;
    _pullBack = 0;
    _blendFromPosition.setFrom(position);
    _blendFromTarget.setFrom(target);
  }

  static double _smooth(double t) {
    final x = t.clamp(0.0, 1.0);
    return x * x * (3 - 2 * x);
  }

  static Vector3 _lerp(Vector3 a, Vector3 b, double k) => a + (b - a) * k;

  Vector3 get _eye => Vector3(playerX, _eyeY, -0.1);

  /// Göz noktasından oyun kurucuya bakış, Y ekseni etrafında [degrees] döndürülmüş.
  Vector3 _lookTarget(double degrees) {
    final eye = _eye;
    final forward = lookAt - eye;
    final angle = degrees * pi / 180;
    final rotated = Vector3(
      forward.x * cos(angle) + forward.z * sin(angle),
      forward.y,
      -forward.x * sin(angle) + forward.z * cos(angle),
    );
    return eye + rotated;
  }

  /// 0 → sola → sağa → 0 bakış açısı (pozitif = sola).
  static double _lookAroundAngle(double t) {
    if (t < 0.25) return _lookAngle * _smooth(t / 0.25);
    if (t < 0.35) return _lookAngle;
    if (t < 0.7) return _lookAngle * (1 - 2 * _smooth((t - 0.35) / 0.35));
    if (t < 0.8) return -_lookAngle;
    return -_lookAngle * (1 - _smooth((t - 0.8) / 0.2));
  }

  @override
  void update(double dt) {
    super.update(dt);
    _time += dt;

    final targetEye = crouched ? crouchEyeY : standEyeY;
    _eyeY += (targetEye - _eyeY) * min(1.0, dt * 12);
    final sway = sin(_time * 1.6) * 0.01;

    switch (_mode) {
      case CameraMode.menu:
        // Menüde yukarıda hafifçe süzül.
        final k = _smooth(_time / 1.2);
        position.setFrom(
          _lerp(
            _blendFromPosition,
            _menuPosition + Vector3(sin(_time * 0.4) * 0.6, 0, 0),
            k,
          ),
        );
        target.setFrom(_lerp(_blendFromTarget, lookAt, k));
      case CameraMode.intro:
        _updateIntro();
        if (_time >= introDuration) _mode = CameraMode.firstPerson;
      case CameraMode.firstPerson:
        final weight = _glanceWeight(dt);
        _pullBack = weight;
        position.setFrom(
          _eye + _sideViewOffset * weight + Vector3(sway, sway, 0),
        );
        target.setFrom(_lerp(lookAt, _glanceTarget?.call() ?? lookAt, weight));
      case CameraMode.loseView:
        final k = _smooth(_time / 0.8);
        position.setFrom(_lerp(_blendFromPosition, _losePosition, k));
        target.setFrom(_lerp(_blendFromTarget, _loseTarget, k));
    }

    if (_shakeTime < _shakeDuration) {
      _shakeTime += dt;
      final amplitude =
          _shakeStrength * max(0.0, 1 - _shakeTime / _shakeDuration);
      final offset = Vector3(
        (_random.nextDouble() * 2 - 1) * amplitude,
        (_random.nextDouble() * 2 - 1) * amplitude,
        0,
      );
      position.add(offset);
      target.add(offset * 0.5);
    }
  }

  /// Bakışın oyun kurucudan hedefe ne kadar döndüğü: 0 → 1 → (takip) → 0.
  double _glanceWeight(double dt) {
    if (_glanceTarget == null) return 0;
    _glanceTime += dt;
    final t = _glanceTime;
    final turned = _smooth(t / _glanceTurn);
    if (_glanceReturnAt == null &&
        ((_glanceUntil?.call() ?? true) || t >= _glanceMax)) {
      _glanceReturnAt = t;
    }
    final returnAt = _glanceReturnAt;
    if (returnAt == null) return turned;
    final k = (t - returnAt) / _glanceReturn;
    if (k >= 1) {
      _glanceTarget = null;
      _glanceUntil = null;
      return 0;
    }
    return turned * (1 - _smooth(k));
  }

  void _updateIntro() {
    final t = _time;
    if (t < _toBehindEnd) {
      // 1) Bulunduğu yerden sıranın arkasına in.
      final k = _smooth(t / _toBehindEnd);
      position.setFrom(_lerp(_blendFromPosition, _behindPosition, k));
      target.setFrom(_lerp(_blendFromTarget, lookAt, k));
    } else if (t < _toEyeEnd) {
      // 2) Oyuncunun kafasına yaklaş: birinci şahıs.
      final k = _smooth((t - _toBehindEnd) / (_toEyeEnd - _toBehindEnd));
      position.setFrom(_lerp(_behindPosition, _eye, k));
      target.setFrom(lookAt);
    } else if (t < _lookStart) {
      position.setFrom(_eye);
      target.setFrom(lookAt);
    } else {
      // 3) Sola, sağa bak (yanımızdakiler görünsün diye geri çekilerek);
      // oyun kurucuya dön.
      final k = (t - _lookStart) / (_lookEnd - _lookStart);
      final angle = _lookAroundAngle(k);
      _pullBack = angle.abs() / _lookAngle;
      position.setFrom(_eye + _sideViewOffset * _pullBack);
      target.setFrom(_lookTarget(angle));
    }
  }
}
