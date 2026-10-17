import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../viewmodel/menu_view_model.dart';
import '../theme.dart';
import '../widgets/buttons.dart';

/// Oyun sırasında sağ üstteki seçenekler. Butona dokununca ya da sola
/// kaydırınca sağdan panel kayarak açılır ve oyun durur; panel sağa
/// kaydırılınca ya da "Devam Et" ile kapanır.
class GameOptions extends StatefulWidget {
  const GameOptions({super.key, required this.menu});

  final MenuViewModel menu;

  @override
  State<GameOptions> createState() => _GameOptionsState();
}

class _GameOptionsState extends State<GameOptions> {
  bool _open = false;

  void _setOpen(bool open) {
    if (open == _open) return;
    setState(() => _open = open);
    if (open) {
      widget.menu.pauseGame();
    } else {
      widget.menu.resumeGame();
    }
  }

  @override
  Widget build(BuildContext context) {
    final menu = widget.menu;
    return SafeArea(
      child: Stack(
        children: [
          // Sağ altta ayna ("Kör Et") ve üstünde kalkan butonu; panel açıkken
          // karartmanın altında.
          Positioned(
            right: 16,
            bottom: 24,
            child: ListenableBuilder(
              listenable: menu,
              builder: (context, _) => Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _PowerButton(
                    icon: 'assets/images/icons/shield.png',
                    charges: menu.shieldCharges,
                    enabled: menu.canUseShield,
                    active: menu.shieldActive,
                    activeColor: const Color(0xFFFFD66B),
                    onTap: menu.useShield,
                  ),
                  const SizedBox(height: 12),
                  _PowerButton(
                    icon: 'assets/images/icons/mirror.png',
                    charges: menu.blindCharges,
                    enabled: menu.canUseBlind,
                    active: menu.blindActive,
                    activeColor: const Color(0xFFB4EEFF),
                    onTap: menu.useBlind,
                  ),
                ],
              ),
            ),
          ),
          // Panel açıkken arkası kararır; dokununca kapanır.
          if (_open)
            Positioned.fill(
              child: GestureDetector(
                onTap: () => _setOpen(false),
                child: const ColoredBox(color: Color(0x66000000)),
              ),
            ),
          Positioned(
            top: 8,
            right: 8,
            child: GestureDetector(
              onHorizontalDragEnd: (d) {
                if ((d.primaryVelocity ?? 0) < 0) _setOpen(true);
              },
              child: IconButton.filled(
                onPressed: () => _setOpen(!_open),
                tooltip: L.options,
                iconSize: 28,
                style: IconButton.styleFrom(
                  backgroundColor: menuPanel,
                  foregroundColor: menuGreen,
                  side: const BorderSide(color: menuGreen, width: 2),
                ),
                icon: Icon(_open ? Icons.close_rounded : Icons.menu_rounded),
              ),
            ),
          ),
          AnimatedPositioned(
            duration: const Duration(milliseconds: 240),
            curve: Curves.easeOutCubic,
            top: 64,
            right: _open ? 8 : -260,
            width: 240,
            child: GestureDetector(
              onHorizontalDragEnd: (d) {
                if ((d.primaryVelocity ?? 0) > 0) _setOpen(false);
              },
              child: Material(
                color: menuPanel,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(18),
                  side: const BorderSide(color: menuGreen, width: 3),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        L.paused,
                        textAlign: TextAlign.center,
                        style: menuFont(26, shadows: menuOutline),
                      ),
                      const SizedBox(height: 12),
                      PanelButton(
                        label: L.resume,
                        icon: Icons.play_arrow_rounded,
                        onPressed: () => _setOpen(false),
                      ),
                      const SizedBox(height: 10),
                      PanelButton(
                        label: L.mainMenu,
                        icon: Icons.home_rounded,
                        onPressed: menu.backToMenu,
                      ),
                      const SizedBox(height: 10),
                      ListenableBuilder(
                        listenable: menu,
                        builder: (context, _) => PanelButton(
                          label: menu.musicOn
                              ? L.musicOnLabel
                              : L.musicOffLabel,
                          icon: menu.musicOn
                              ? Icons.music_note_rounded
                              : Icons.music_off_rounded,
                          onPressed: menu.toggleMusic,
                        ),
                      ),
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

/// Oyun sırasında sağ alttaki güç butonu (ayna: "Kör Et", kalkan): hakkı
/// varsa dokununca etkinleşir; etkinken çerçevesi [activeColor] olur. Kalan
/// hak sayısı köşede yazar.
class _PowerButton extends StatelessWidget {
  const _PowerButton({
    required this.icon,
    required this.charges,
    required this.enabled,
    required this.active,
    required this.activeColor,
    required this.onTap,
  });

  final String icon;
  final int charges;
  final bool enabled;
  final bool active;
  final Color activeColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: enabled || active ? 1 : 0.45,
      child: Material(
        color: menuPanel,
        shape: CircleBorder(
          side: BorderSide(color: active ? activeColor : menuGreen, width: 3),
        ),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: enabled ? onTap : null,
          child: SizedBox(
            width: 64,
            height: 64,
            child: Stack(
              children: [
                Center(
                  child: Image.asset(
                    icon,
                    width: 42,
                    height: 42,
                    cacheWidth: 128,
                  ),
                ),
                Positioned(
                  right: 4,
                  bottom: 2,
                  child: Text(
                    '$charges',
                    style: menuFont(
                      18,
                      color: Colors.white,
                      shadows: menuOutline,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
