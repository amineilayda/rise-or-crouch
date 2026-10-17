import 'dart:math';
import 'dart:ui';

import 'package:flame/components.dart';

/// Renk geçişli gökyüzü, parlayan güneş ve yavaşça kayan bulutlar.
///
/// 3D sahnenin arka planı şeffaf temizlendiği için bu 2D bileşen oyunun
/// en arkasında çizilir ve 3D zeminin üstünde kalan her yerde görünür.
class Sky extends Component with HasGameReference {
  Color _top = const Color(0xFF3E9BE6);
  Color _horizon = const Color(0xFFCFEFFF);
  bool _sunAndClouds = true;

  /// Bölüme göre gökyüzü renkleri; zindanda güneş ve bulut yok.
  void configure({
    required Color top,
    required Color horizon,
    required bool sunAndClouds,
  }) {
    _top = top;
    _horizon = horizon;
    _sunAndClouds = sunAndClouds;
    if (isMounted) {
      _lastSize = Vector2.zero();
      onGameResize(game.size);
    }
  }

  final Random _random = Random();
  final List<_Cloud> _clouds = [];
  final Paint _skyPaint = Paint();
  final Paint _sunPaint = Paint()..color = const Color(0xFFFFF6C8);
  final Paint _glowPaint = Paint();
  final Paint _cloudPaint = Paint()..color = const Color(0xF2FFFFFF);
  Vector2 _lastSize = Vector2.zero();

  @override
  void onGameResize(Vector2 size) {
    super.onGameResize(size);
    if (_lastSize == size) return;
    _lastSize = size.clone();
    _skyPaint.shader = Gradient.linear(Offset.zero, Offset(0, size.y * 0.55), [
      _top,
      _horizon,
    ]);
    final sun = _sunCenter(size);
    _glowPaint.shader = Gradient.radial(sun, size.x * 0.35, const [
      Color(0x99FFF3B0),
      Color(0x00FFF3B0),
    ]);
    _clouds
      ..clear()
      ..addAll(List.generate(6, (_) => _Cloud.random(_random, size)));
  }

  Offset _sunCenter(Vector2 size) => Offset(size.x * 0.78, size.y * 0.12);

  @override
  void update(double dt) {
    final width = game.size.x;
    for (final cloud in _clouds) {
      cloud.x += cloud.speed * dt;
      if (cloud.x - cloud.scale * 120 > width) {
        cloud.x = -cloud.scale * 120;
      }
    }
  }

  @override
  void render(Canvas canvas) {
    final size = game.size;
    canvas.drawRect(Rect.fromLTWH(0, 0, size.x, size.y), _skyPaint);
    if (!_sunAndClouds) return;
    final sun = _sunCenter(size);
    canvas.drawCircle(sun, size.x * 0.35, _glowPaint);
    canvas.drawCircle(sun, size.x * 0.07, _sunPaint);
    for (final cloud in _clouds) {
      cloud.render(canvas, _cloudPaint);
    }
  }
}

/// Üst üste binmiş üç elipsten oluşan basit bir bulut.
class _Cloud {
  _Cloud(this.x, this.y, this.scale, this.speed);

  factory _Cloud.random(Random random, Vector2 size) => _Cloud(
    random.nextDouble() * size.x,
    size.y * (0.05 + random.nextDouble() * 0.3),
    0.6 + random.nextDouble() * 0.8,
    6 + random.nextDouble() * 10,
  );

  double x;
  final double y;
  final double scale;
  final double speed;

  void render(Canvas canvas, Paint paint) {
    final s = scale;
    canvas
      ..drawOval(
        Rect.fromCenter(center: Offset(x, y), width: 130 * s, height: 46 * s),
        paint,
      )
      ..drawOval(
        Rect.fromCenter(
          center: Offset(x - 28 * s, y - 16 * s),
          width: 70 * s,
          height: 50 * s,
        ),
        paint,
      )
      ..drawOval(
        Rect.fromCenter(
          center: Offset(x + 22 * s, y - 22 * s),
          width: 80 * s,
          height: 60 * s,
        ),
        paint,
      );
  }
}
