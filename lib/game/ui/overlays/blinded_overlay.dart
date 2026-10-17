import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../theme.dart';

/// Rakip seni kör edince: ekran bulanıklaşır, ortada üstü çizili göz
/// (assets/images/icons/blind.png) nabız gibi atar, altında kimin yaptığı yazar.
/// Dokunuşları engellemez; kaydırmalar oyuna geçer.
class BlindedOverlay extends StatefulWidget {
  const BlindedOverlay({super.key, required this.name});

  final String name;

  @override
  State<BlindedOverlay> createState() => _BlindedOverlayState();
}

class _BlindedOverlayState extends State<BlindedOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 600),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: TweenAnimationBuilder<double>(
        // Bulanıklık bir anda değil, yumuşakça gelir.
        tween: Tween(begin: 0, end: 1),
        duration: const Duration(milliseconds: 350),
        builder: (context, t, child) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 7 * t, sigmaY: 7 * t),
          child: ColoredBox(
            color: Color.fromRGBO(30, 12, 48, 0.25 * t),
            child: Opacity(opacity: t, child: child),
          ),
        ),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AnimatedBuilder(
                animation: _pulse,
                builder: (context, child) => Transform.scale(
                  scale: 0.9 + 0.15 * _pulse.value,
                  child: child,
                ),
                child: Image.asset(
                  'assets/images/icons/blind.png',
                  width: 110,
                  height: 110,
                  cacheWidth: 256,
                  // Siyah simge karanlık sahnede görünsün diye beyaza boyanır.
                  color: Colors.white,
                  colorBlendMode: BlendMode.srcIn,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                L.blindedBy(widget.name),
                textAlign: TextAlign.center,
                style: menuFont(24, color: Colors.white, shadows: menuOutline),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
