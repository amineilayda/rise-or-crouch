import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../l10n/strings.dart';
import '../../level_design/levels.dart';
import '../../viewmodel/menu_view_model.dart';
import '../theme.dart';
import '../widgets/buttons.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.menu});

  final MenuViewModel menu;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: Column(
        children: [
          const SizedBox(height: 24),
          Text(
            'Rise or Crouch',
            textAlign: TextAlign.center,
            style: menuFont(52, shadows: menuOutline),
          ),
          const SizedBox(height: 4),
          Text(
            L.subtitle,
            textAlign: TextAlign.center,
            style: menuFont(24, shadows: menuOutline),
          ),
          const Spacer(),
          _SwipeHint(level: menu.swipeLevel),
          const SizedBox(height: 18),
          MenuButton(
            label: L.newGame,
            icon: Icons.refresh_rounded,
            onPressed: menu.newGame,
          ),
          const SizedBox(height: 16),
          MenuButton(
            label: L.levels,
            icon: Icons.grid_view_rounded,
            onPressed: menu.showLevels,
          ),
          const SizedBox(height: 16),
          MenuButton(
            label: L.shop,
            icon: Icons.storefront_rounded,
            onPressed: menu.showShop,
          ),
          const SizedBox(height: 20),
          // Talimat ince bir fontla: başlık ve butonlarla yarışmasın.
          Text(
            L.swipeHint,
            textAlign: TextAlign.center,
            style: GoogleFonts.quicksand(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.3,
              color: menuGreen,
              shadows: const [Shadow(blurRadius: 6, color: Colors.black87)],
            ),
          ),
        ],
      ),
    );
  }
}

/// Butonların üstünde: arkadaki bölümü oynamak için kaydır çağrısı. Ok
/// yukarı aşağı süzülerek kaydırmayı hatırlatır.
class _SwipeHint extends StatefulWidget {
  const _SwipeHint({required this.level});

  final LevelConfig level;

  @override
  State<_SwipeHint> createState() => _SwipeHintState();
}

class _SwipeHintState extends State<_SwipeHint>
    with SingleTickerProviderStateMixin {
  late final AnimationController _bob = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _bob.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AnimatedBuilder(
          animation: _bob,
          builder: (context, child) => Transform.translate(
            offset: Offset(0, -8 * Curves.easeInOut.transform(_bob.value)),
            child: child,
          ),
          child: const Icon(
            Icons.swipe_vertical_rounded,
            size: 34,
            color: Colors.white,
            shadows: [Shadow(blurRadius: 6, color: Colors.black87)],
          ),
        ),
        const SizedBox(height: 4),
        Text(L.swipeToPlay, style: menuFont(24, shadows: menuOutline)),
        Text(
          L.levelWithName(widget.level.number),
          style: GoogleFonts.quicksand(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: Colors.white,
            shadows: const [Shadow(blurRadius: 6, color: Colors.black87)],
          ),
        ),
      ],
    );
  }
}
