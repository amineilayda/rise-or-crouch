import 'dart:math';
import 'dart:ui';

import 'package:flame_3d/core.dart';
import 'package:flame_3d/graphics.dart';
import 'package:flame_3d/model.dart';
import 'package:flutter/foundation.dart';

import 'pose.dart';

class Character extends ModelComponent {
  Character({
    required super.model,
    super.position,
    super.rotation,
    super.scale,
  });

  bool _crouched = false;

  double _oneShotLeft = 0;
  String? _next;

  /// Tek seferlik animasyon bitti ve "sonra" verilmediyse son karesinde bekle.
  bool _holding = false;

  bool? _pendingCrouch;
  double _pendingDelay = 0;

  /// Oyun kurucunun şu anki duruşu: Idle, Deve ya da Cuce.
  String _leaderPose = 'Idle';

  /// false iken çizilmez (birinci şahısta oyuncunun kendi modeli).
  bool visible = true;

  /// Yanıp oyundan çıktı mı (NPC'ler için).
  bool eliminated = false;
  double? _failIn;

  /// Yanan oyuncu sıradan çıkarken yürüme hızı (m/sn) ve gideceği nokta.
  static const double walkSpeed = 1.6;
  Vector3? _walkTarget;
  bool _walking = false;

  /// Başlangıç yeri ve yönü; tur sıfırlanınca buraya döner.
  late final Vector3 _home;
  late final Quaternion _homeRotation;

  @override
  void renderTree(Canvas canvas) {
    if (visible) super.renderTree(canvas);
  }

  @override
  Future<void> onLoad() async {
    await super.onLoad();
    _home = position.clone();
    _homeRotation = rotation.clone();
    playAnimationByName('Idle');
  }

  static bool _drawErrorReported = false;

  @override
  void draw(covariant RenderContext3D context) {
    try {
      super.draw(context);
    } on Object catch (error, stack) {
      if (!_drawErrorReported) {
        _drawErrorReported = true;
        debugPrint(
          'Character.draw hatası (animasyon: $_debugAnimation): $error\n$stack',
        );
      }
    }
  }

  String _debugAnimation = 'Idle';

  @override
  void playAnimationByName(String name, {bool resetClock = true}) {
    _debugAnimation = name;
    super.playAnimationByName(name, resetClock: resetClock);
  }

  void setCrouched(bool value, {double delay = 0}) {
    if (delay > 0) {
      _pendingCrouch = value;
      _pendingDelay = delay;
      return;
    }
    _pendingCrouch = null;
    if (value == _crouched) return;
    _crouched = value;
    _playOnce(
      value ? 'Crouch' : 'StandUp',
      then: value ? 'CrouchIdle' : 'Idle',
    );
  }

  /// Oyun kurucunun hareketi: DEVE'de kollar havaya, CÜCE'de çömelip aşağı
  /// bastırır. Aynı komut tekrar gelirse hareketi bir kez daha vurgular.
  /// Animasyonlar tools/make_animations.py'de `L_<nereden>_<nereye>` adıyla.
  void gesture(Pose pose) {
    final target = pose == Pose.stand ? 'Deve' : 'Cuce';
    _playOnce('L_${_leaderPose}_$target');
    _leaderPose = target;
  }

  void fail() => _playOnce('Fail');

  /// [delay] saniye sonra yanar: başını eğip üzülür, sonra [walkTo]'ya doğru
  /// yürüyüp (yüzü yürüdüğü yöne dönük) orada kaybolur.
  void eliminateAfter(double delay, {required Vector3 walkTo}) {
    eliminated = true;
    _failIn = delay;
    _walkTarget = walkTo;
  }

  /// Sahneden çıktı mı (yürüyüp kayboldu).
  bool get gone => eliminated && !visible;

  /// Önceki bölümde yanmış: bu bölümde sırada yok.
  void removeFromRow() {
    eliminated = true;
    visible = false;
  }

  void cheer() {
    _oneShotLeft = 0;
    _holding = false;
    playAnimationByName('Cheer');
  }

  void resetPose() {
    _crouched = false;
    _pendingCrouch = null;
    _oneShotLeft = 0;
    _next = null;
    _holding = false;
    _leaderPose = 'Idle';
    eliminated = false;
    _failIn = null;
    _walkTarget = null;
    _walking = false;
    visible = true;
    position.setFrom(_home);
    rotation.setFrom(_homeRotation);
    playAnimationByName('Idle');
  }

  /// [name]'i bir kez oynatır; bitince [then] döngüsüne geçer, [then] yoksa
  /// son karede bekler.
  void _playOnce(String name, {String? then}) {
    playAnimationByName(name);
    _oneShotLeft = _duration(name);
    _next = then;
    _holding = false;
  }

  /// Yürüyüşe başla: modeli gideceği yöne çevir (model kendi +Z'sine bakıyor).
  void _startWalking() {
    final target = _walkTarget;
    if (target == null) return;
    final direction = target - position;
    rotation.setFrom(
      Quaternion.axisAngle(Vector3(0, 1, 0), atan2(direction.x, direction.z)),
    );
    _walking = true;
  }

  double _duration(String name) =>
      model.animations.firstWhere((a) => a.name == name).lastTime;

  @override
  void update(double dt) {
    if (_pendingCrouch != null) {
      _pendingDelay -= dt;
      if (_pendingDelay <= 0) setCrouched(_pendingCrouch!);
    }
    final failIn = _failIn;
    if (failIn != null) {
      _failIn = failIn - dt;
      if (_failIn! <= 0) {
        _failIn = null;
        _pendingCrouch = null;
        if (_walkTarget != null) {
          _playOnce('Fail', then: 'Walk');
        } else {
          fail();
        }
      }
    }
    final walkTarget = _walkTarget;
    if (_walking && walkTarget != null) {
      final toTarget = walkTarget - position;
      final step = walkSpeed * dt;
      if (toTarget.length <= step) {
        _walking = false;
        visible = false;
      } else {
        position.add(toTarget.normalized() * step);
      }
    }
    if (_holding) {
      super.update(0);
      return;
    }
    if (_oneShotLeft > 0) {
      _oneShotLeft -= dt;
      // Animasyon saati sona gelip başa sarmadan önce geç ya da dur.
      if (_oneShotLeft <= 0) {
        final next = _next;
        _next = null;
        if (next == null) {
          _holding = true;
        } else {
          playAnimationByName(next);
          if (next == 'Walk') _startWalking();
        }
        super.update(0);
        return;
      }
    }
    super.update(dt);
  }
}
