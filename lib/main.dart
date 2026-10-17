import 'package:flame/flame.dart';
import 'package:flame/game.dart';
import 'package:flame_3d/graphics.dart';
import 'package:flutter/material.dart';

import 'game/l10n/strings.dart';
import 'game/logic/rise_crouch_game.dart';
import 'game/ui/overlays/blinded_overlay.dart';
import 'game/ui/overlays/game_options.dart';
import 'game/ui/overlays/result_card.dart';
import 'game/ui/pages/main_menu.dart';
import 'game/viewmodel/menu_view_model.dart';
import 'game/viewmodel/shop_view_model.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await GpuBackend.initialize();
  await Flame.device.fullScreen();
  await Flame.device.setPortrait();

  // Oyun ve menünün ViewModel'i bir kez kurulur; arayüz ViewModel'i dinler.
  final game = RiseCrouchGame();
  final menu = MenuViewModel(game);
  final shop = ShopViewModel(game.profile);

  runApp(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      // Arapça gibi sağdan sola yazılan dillerde arayüz de sağdan sola akar.
      builder: (context, child) => ValueListenableBuilder(
        valueListenable: game.profile.language,
        builder: (context, language, _) => Directionality(
          textDirection: language.rtl ? TextDirection.rtl : TextDirection.ltr,
          child: child!,
        ),
      ),
      home: GameWidget<RiseCrouchGame>(
        game: game,
        initialActiveOverlays: const [RiseCrouchGame.overlayMenu],

        overlayBuilderMap: {
          RiseCrouchGame.overlayMenu: (context, game) => Material(
            type: MaterialType.transparency,
            child: MainMenu(menu: menu, shop: shop),
          ),
          RiseCrouchGame.overlayBlinded: (context, game) =>
              BlindedOverlay(name: game.blindedByName),
          RiseCrouchGame.overlayOptions: (context, game) => Material(
            type: MaterialType.transparency,
            child: GameOptions(menu: menu),
          ),
          RiseCrouchGame.overlayGameOver: (context, game) => Material(
            type: MaterialType.transparency,
            child: ResultCard(
              title: L.youLost,
              subtitle: game.loseReason,
              primaryLabel: L.playAgain,
              onPrimary: game.startGame,
              onMenu: menu.backToMenu,
            ),
          ),
          RiseCrouchGame.overlayLevelComplete: (context, game) => Material(
            type: MaterialType.transparency,
            child: ResultCard(
              title: L.levelComplete(game.level.number),
              subtitle: '${L.coinsEarned(game.lastReward)}\n${L.nextIsHarder}',
              primaryLabel: L.goToLevel(game.level.number + 1),
              onPrimary: game.nextLevel,
              onMenu: menu.backToMenu,
            ),
          ),
          RiseCrouchGame.overlayFinished: (context, game) => Material(
            type: MaterialType.transparency,
            child: ResultCard(
              title: L.congrats,
              subtitle: '${L.coinsEarned(game.lastReward)}\n${L.allLevelsDone}',
              primaryLabel: L.startOver,
              onPrimary: game.restartFromFirstLevel,
              onMenu: menu.backToMenu,
            ),
          ),
        },
      ),
    ),
  );
}
