import 'dart:math';

import 'package:flame_3d/game.dart';
import 'package:flame_3d/model.dart';

/// Yananların içine girip kaybolduğu kapı: kule gövdesi ve menteşeleri
/// etrafında dönen iki kanat (tools/build_gate.py). Kanatlar kapalı durur;
/// [wantOpen] true iken dışa doğru açılır, false olunca kapanır.
///
/// Parçalar dünyaya ayrı ayrı eklenir ([parts]); oyun her karede [update]'i
/// çağırır.
class Gate {
  Gate({
    required Model body,
    required Model leftDoor,
    required Model rightDoor,
    required Vector3 position,
    required Quaternion rotation,
  }) : _rotation = rotation,
       _leftDoor = ModelComponent(
         model: leftDoor,
         position: position + rotation.rotated(_leftHinge),
         rotation: rotation.clone(),
       ),
       _rightDoor = ModelComponent(
         model: rightDoor,
         position: position + rotation.rotated(_rightHinge),
         rotation: rotation.clone(),
       ),
       _body = ModelComponent(
         model: body,
         position: position,
         rotation: rotation,
       );

  /// Menteşelerin kapının merkezine göre yeri (build_gate.py: GATE_HINGE).
  static final Vector3 _leftHinge = Vector3(-0.664, 0, -1.058);
  static final Vector3 _rightHinge = Vector3(0.664, 0, -1.058);

  /// Tam açıkken kanatların dönüş açısı ve açılma / kapanma süresi.
  static const double _openAngle = 80 * pi / 180;
  static const double _swingTime = 0.45;

  final Quaternion _rotation;
  final ModelComponent _body;
  final ModelComponent _leftDoor;
  final ModelComponent _rightDoor;

  List<ModelComponent> get parts => [_body, _leftDoor, _rightDoor];

  Vector3 get position => _body.position;

  bool wantOpen = false;

  /// 0 kapalı, 1 tam açık.
  double _open = 0;

  void update(double dt) {
    final target = wantOpen ? 1.0 : 0.0;
    if (_open == target) return;
    final step = dt / _swingTime;
    _open = wantOpen ? min(1, _open + step) : max(0, _open - step);
    // Yumuşak başlayıp yumuşak durur.
    final angle = _openAngle * (0.5 - 0.5 * cos(pi * _open));
    final up = Vector3(0, 1, 0);
    // Kanatlar dışa (kapının baktığı yöne) açılır: sol kanat +, sağ kanat -.
    _leftDoor.rotation.setFrom(_rotation * Quaternion.axisAngle(up, angle));
    _rightDoor.rotation.setFrom(_rotation * Quaternion.axisAngle(up, -angle));
  }

  /// Kapalı hâle döner (yeni tur).
  void reset() {
    wantOpen = false;
    _open = 0;
    _leftDoor.rotation.setFrom(_rotation);
    _rightDoor.rotation.setFrom(_rotation);
  }
}
