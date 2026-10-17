import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../../viewmodel/menu_view_model.dart';
import '../theme.dart';
import '../widgets/buttons.dart';

/// 13 dil, her biri kendi dilindeki adıyla; seçili olan yeşil çerçeveli.
class LanguagePage extends StatelessWidget {
  const LanguagePage({super.key, required this.menu});

  final MenuViewModel menu;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: Column(
        children: [
          const SizedBox(height: 24),
          Text(L.languageLabel, style: menuFont(44, shadows: menuOutline)),
          const SizedBox(height: 20),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: 3.2,
              padding: EdgeInsets.zero,
              children: [
                for (final language in menu.languages)
                  _LanguageTile(
                    language: language,
                    selected: language == menu.language,
                    onTap: () => menu.setLanguage(language),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
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

class _LanguageTile extends StatelessWidget {
  const _LanguageTile({
    required this.language,
    required this.selected,
    required this.onTap,
  });

  final AppLanguage language;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: menuPanel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: selected ? menuGreen : const Color(0xFF5E6A58),
          width: selected ? 3 : 2,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Center(
          // Her dilin adı kendi yazısıyla; menü fontunda olmayan harfler
          // için sistem fontu kullanılsın diye sade bir yazı tipi.
          child: Text(
            language.nativeName,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: selected ? menuGreen : Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
