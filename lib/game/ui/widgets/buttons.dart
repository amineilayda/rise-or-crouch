import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../viewmodel/menu_view_model.dart';
import '../theme.dart';

class PanelButton extends StatelessWidget {
  const PanelButton({
    super.key,
    required this.label,
    required this.icon,
    required this.onPressed,
  });

  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      child: OutlinedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 24),
        label: Text(label),
        style: OutlinedButton.styleFrom(
          foregroundColor: menuGreen,
          side: const BorderSide(color: menuGreen, width: 2),
          textStyle: menuFont(20),
        ),
      ),
    );
  }
}

/// Ana menüdeki büyük buton: koyu yeşil zemin, yeşil yazı.
class MenuButton extends StatelessWidget {
  const MenuButton({
    super.key,
    required this.label,
    required this.icon,
    required this.onPressed,
  });

  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 280,
      height: 68,
      child: FilledButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 30),
        label: Text(label),
        style: FilledButton.styleFrom(
          backgroundColor: menuPanel,
          foregroundColor: menuGreen,
          side: const BorderSide(color: menuGreen, width: 3),
          textStyle: menuFont(28),
        ),
      ),
    );
  }
}

class BigButton extends StatelessWidget {
  const BigButton({super.key, required this.label, required this.onPressed});

  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 260,
      height: 60,
      child: FilledButton(
        onPressed: onPressed,
        style: FilledButton.styleFrom(
          backgroundColor: const Color(0xFFFF8F00),
          textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
        child: Text(label),
      ),
    );
  }
}

/// Menünün sağ üstündeki müzik aç / kapa butonu.
class MusicButton extends StatelessWidget {
  const MusicButton({super.key, required this.menu});

  final MenuViewModel menu;

  @override
  Widget build(BuildContext context) {
    final on = menu.musicOn;
    return IconButton.filled(
      onPressed: menu.toggleMusic,
      tooltip: on ? L.turnMusicOff : L.turnMusicOn,
      iconSize: 28,
      style: IconButton.styleFrom(
        backgroundColor: menuPanel,
        foregroundColor: on ? menuGreen : const Color(0xFF7A8574),
        side: BorderSide(
          color: on ? menuGreen : const Color(0xFF7A8574),
          width: 2,
        ),
      ),
      icon: Icon(on ? Icons.music_note_rounded : Icons.music_off_rounded),
    );
  }
}

/// Menünün sağ üstünde, müzik butonunun yanında dil seçimi.
class LanguageButton extends StatelessWidget {
  const LanguageButton({super.key, required this.menu});

  final MenuViewModel menu;

  @override
  Widget build(BuildContext context) {
    return IconButton.filled(
      onPressed: menu.showLanguages,
      tooltip: L.languageLabel,
      iconSize: 28,
      style: IconButton.styleFrom(
        backgroundColor: menuPanel,
        foregroundColor: menuGreen,
        side: const BorderSide(color: menuGreen, width: 2),
      ),
      icon: const Icon(Icons.language_rounded),
    );
  }
}
