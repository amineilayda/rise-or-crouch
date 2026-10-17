import 'dart:math';
import 'dart:ui';

import 'package:flame/components.dart';

/// Ekranın önünde yağan kar. 3D sahnenin üstünde, HUD'un altında çizilir.
/// Yakındaki taneler büyük ve hızlı, uzaktakiler küçük ve yavaş düşer.
class Snowfall extends Component with HasGameReference {
  Snowfall({this.count = 140});

  final int count;

  /// false iken çizilmez ve güncellenmez (karsız bölümler).
  bool active = false;

  final Random _random = Random();
  final List<_Flake> _flakes = [];
  final Paint _paint = Paint();
  double _time = 0;

  @override
  void onGameResize(Vector2 size) {
    super.onGameResize(size);
    if (_flakes.isEmpty) {
      _flakes.addAll(
        List.generate(
          count,
          (_) => _Flake.random(_random, size, anywhere: true),
        ),
      );
    }
  }

  @override
  void update(double dt) {
    if (!active) return;
    _time += dt;
    final size = game.size;
    for (var i = 0; i < _flakes.length; i++) {
      final flake = _flakes[i];
      flake.y += flake.speed * dt;
      if (flake.y - flake.radius > size.y) {
        _flakes[i] = _Flake.random(_random, size, anywhere: false);
      }
    }
  }

  @override
  void render(Canvas canvas) {
    if (!active) return;
    for (final flake in _flakes) {
      // Rüzgârda hafifçe sağa sola salınır.
      final x =
          flake.x + sin(_time * flake.swaySpeed + flake.phase) * flake.sway;
      _paint.color = Color.fromRGBO(255, 255, 255, flake.alpha);
      canvas.drawCircle(Offset(x, flake.y), flake.radius, _paint);
    }
  }
}

class _Flake {
  _Flake(
    this.x,
    this.y,
    this.radius,
    this.speed,
    this.sway,
    this.swaySpeed,
    this.phase,
    this.alpha,
  );

  /// [anywhere] true ise ekranın herhangi bir yerinde, değilse üstünde başlar.
  factory _Flake.random(Random random, Vector2 size, {required bool anywhere}) {
    final depth = random.nextDouble(); // 0 uzak, 1 yakın
    final radius = 1.2 + depth * 3.0;
    return _Flake(
      random.nextDouble() * size.x,
      anywhere
          ? random.nextDouble() * size.y
          : -radius - random.nextDouble() * 40,
      radius,
      35 + depth * 85,
      6 + random.nextDouble() * 14,
      0.6 + random.nextDouble() * 1.2,
      random.nextDouble() * 2 * pi,
      0.55 + depth * 0.4,
    );
  }

  final double x;
  double y;
  final double radius;
  final double speed;
  final double sway;
  final double swaySpeed;
  final double phase;
  final double alpha;
}
