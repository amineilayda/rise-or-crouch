import 'dart:math';

import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../viewmodel/menu_view_model.dart';
import '../theme.dart';
import '../widgets/buttons.dart';

/// Bölüm haritası: 9 kare yılan gibi dizilir (1→2→3, 6←5←4, 7→8→9) ve
/// aralarında oklu borular uzanır.
class LevelsPage extends StatelessWidget {
  const LevelsPage({super.key, required this.menu});

  final MenuViewModel menu;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: Column(
        children: [
          const SizedBox(height: 24),
          Text(L.levels, style: menuFont(48, shadows: menuOutline)),
          const Spacer(),
          _LevelMap(menu: menu),
          const Spacer(),
          MenuButton(
            label: L.back,
            icon: Icons.arrow_back_rounded,
            onPressed: menu.showHome,
          ),
        ],
      ),
    );
  }
}

class _LevelMap extends StatelessWidget {
  const _LevelMap({required this.menu});

  final MenuViewModel menu;

  static const int _columns = 3;
  static const double _tile = 76;
  static const double _gap = 34;
  static const double _pipe = 14;
  static const double _size = _columns * _tile + (_columns - 1) * _gap;

  /// i. bölümün ızgaradaki yeri (satır, sütun): tek satırlar sağdan sola.
  static (int, int) _cell(int i) {
    final row = i ~/ _columns;
    final col = i % _columns;
    return (row, row.isOdd ? _columns - 1 - col : col);
  }

  static Offset _origin(int i) {
    final (row, col) = _cell(i);
    return Offset(col * (_tile + _gap), row * (_tile + _gap));
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: _size,
      height: _size,
      child: Stack(
        children: [
          // Borular karelerin altında: i'den i+1'e.
          for (var i = 0; i < MenuViewModel.levelSlots - 1; i++)
            _pipeBetween(i),
          for (var i = 0; i < MenuViewModel.levelSlots; i++)
            Positioned(
              left: _origin(i).dx,
              top: _origin(i).dy,
              width: _tile,
              height: _tile,
              child: _LevelTile(
                number: i + 1,
                state: menu.tileState(i),
                onPressed: () => menu.playLevel(i),
              ),
            ),
        ],
      ),
    );
  }

  /// Bitirilmiş bölümden çıkan boru yeşil, diğerleri gri.
  Widget _pipeBetween(int i) {
    final a = _origin(i);
    final b = _origin(i + 1);
    final lit = menu.isPathLit(i);
    final color = lit ? menuGreen : const Color(0xFF5E6A58);
    final Rect rect;
    final IconData arrow;
    if (a.dy == b.dy) {
      // Yatay boru: iki karenin arasındaki boşlukta, ortada.
      final left = min(a.dx, b.dx) + _tile - 6;
      rect = Rect.fromLTWH(left, a.dy + (_tile - _pipe) / 2, _gap + 12, _pipe);
      arrow = b.dx > a.dx
          ? Icons.chevron_right_rounded
          : Icons.chevron_left_rounded;
    } else {
      // Dikey boru: satır sonunda aşağı iner.
      rect = Rect.fromLTWH(
        a.dx + (_tile - _pipe) / 2,
        a.dy + _tile - 6,
        _pipe,
        _gap + 12,
      );
      arrow = Icons.expand_more_rounded;
    }
    return Positioned.fromRect(
      rect: rect,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(3),
          border: Border.all(color: menuGreenDark, width: 2),
        ),
        child: OverflowBox(
          maxWidth: 26,
          maxHeight: 26,
          child: Icon(
            arrow,
            size: 22,
            color: lit ? menuGreenDark : const Color(0xFF2C3329),
          ),
        ),
      ),
    );
  }
}

/// Bölüm karesi: sıradaki bölüm yeşil ve tıklanabilir; bitirilenler ✓,
/// sonrakiler kilitli, henüz yapılmamışlar soluk kilitli.
class _LevelTile extends StatelessWidget {
  const _LevelTile({
    required this.number,
    required this.state,
    required this.onPressed,
  });

  final int number;
  final LevelTileState state;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final playable = state == LevelTileState.current;
    final color = switch (state) {
      LevelTileState.current => menuGreen,
      LevelTileState.done => const Color(0xFF5FA83A),
      LevelTileState.locked || LevelTileState.soon => const Color(0xFF7A8574),
    };
    return Material(
      color: menuPanel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: state == LevelTileState.soon
              ? color.withValues(alpha: 0.5)
              : color,
          width: playable ? 4 : 3,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: playable ? onPressed : null,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('$number', style: menuFont(34, color: color)),
            switch (state) {
              LevelTileState.current => Icon(
                Icons.play_arrow_rounded,
                size: 20,
                color: color,
              ),
              LevelTileState.done => Icon(
                Icons.check_rounded,
                size: 20,
                color: color,
              ),
              LevelTileState.locked => Icon(
                Icons.lock_rounded,
                size: 18,
                color: color,
              ),
              LevelTileState.soon => Icon(
                Icons.lock_rounded,
                size: 18,
                color: color.withValues(alpha: 0.5),
              ),
            },
          ],
        ),
      ),
    );
  }
}
