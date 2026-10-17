import 'package:flutter/material.dart';

import '../../viewmodel/menu_view_model.dart';
import '../../viewmodel/shop_view_model.dart';
import '../widgets/buttons.dart';
import '../widgets/coin_badge.dart';
import 'home_page.dart';
import 'language_page.dart';
import 'levels_page.dart';
import 'shop_page.dart';

/// Ana menü: "Yeni Oyun" ve "Bölümler"; ekranı kaydırmak arkadaki bölümü
/// başlatır. Hangi sayfanın açık olduğu ve bütün aksiyonlar [MenuViewModel]'de.
class MainMenu extends StatelessWidget {
  const MainMenu({super.key, required this.menu, required this.shop});

  final MenuViewModel menu;
  final ShopViewModel shop;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: menu,
      builder: (context, _) => SafeArea(
        child: Stack(
          fit: StackFit.expand,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
              child: switch (menu.page) {
                MenuPage.levels => LevelsPage(menu: menu),
                MenuPage.shop => ShopPage(shop: shop, onBack: menu.showHome),
                MenuPage.language => LanguagePage(menu: menu),
                // Ana sayfada ekranın boş bir yerini yukarı ya da aşağı
                // kaydırmak arkadaki bölümü başlatır.
                MenuPage.home => GestureDetector(
                  behavior: HitTestBehavior.translucent,
                  onVerticalDragEnd: (details) {
                    if ((details.primaryVelocity ?? 0).abs() > 200) {
                      menu.playSwipedLevel();
                    }
                  },
                  child: HomePage(menu: menu),
                ),
              },
            ),
            Positioned(top: 8, left: 8, child: CoinBadge(coins: menu.coins)),
            Positioned(top: 8, right: 8, child: MusicButton(menu: menu)),
            Positioned(top: 8, right: 64, child: LanguageButton(menu: menu)),
          ],
        ),
      ),
    );
  }
}
