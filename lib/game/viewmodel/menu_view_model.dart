import 'package:flutter/foundation.dart';

import '../data/player_profile.dart';
import '../l10n/strings.dart';
import '../level_design/levels.dart';
import '../logic/rise_crouch_game.dart';

/// Ana menüde hangi sayfanın açık olduğu.
enum MenuPage { home, levels, shop, language }

/// Bölüm haritasındaki bir karenin durumu.
enum LevelTileState {
  /// Bitirildi (✓), şu an oynanamaz.
  done,

  /// Oynanabilir (sıradaki bölüm ya da hepsi açıkken herhangi biri).
  current,

  /// Henüz sırası gelmedi.
  locked,

  /// Henüz yapılmadı ("yakında").
  soon,
}

/// Ana menünün, bölüm haritasının ve oyun içi duraklatma menüsünün
/// ViewModel'i. Arayüz yalnızca bunu dinler ve bunun metotlarını çağırır;
/// oyunun ve profilin içini bilmez.
class MenuViewModel extends ChangeNotifier {
  MenuViewModel(this._game) {
    _profile.completedLevels.addListener(notifyListeners);
    _profile.musicOn.addListener(notifyListeners);
    _profile.coins.addListener(notifyListeners);
    _game.menuLevel.addListener(notifyListeners);
    _profile.blindCharges.addListener(notifyListeners);
    _game.blindActive.addListener(notifyListeners);
    _profile.shieldCharges.addListener(notifyListeners);
    _game.shieldActive.addListener(notifyListeners);
    _profile.language.addListener(notifyListeners);
  }

  final RiseCrouchGame _game;
  PlayerProfile get _profile => _game.profile;

  /// Haritadaki kare sayısı; levels.dart'ta tanımlı olmayanlar "yakında".
  static const int levelSlots = 9;

  // --- Durum -----------------------------------------------------------------

  MenuPage _page = MenuPage.home;
  MenuPage get page => _page;

  /// Menünün arkasındaki sahnenin bölümü; kaydırınca bu oynanır.
  LevelConfig get swipeLevel => levels[_game.menuLevel.value];

  bool get musicOn => _profile.musicOn.value;
  int get coins => _profile.coins.value;

  /// Oyun içi ayna butonu: kaç "Kör Et" hakkı var, şu an kör mü.
  int get blindCharges => _profile.blindCharges.value;
  bool get blindActive => _game.blindActive.value;
  bool get canUseBlind => blindCharges > 0 && !blindActive;

  /// Oyun içi kalkan butonu: kaç "Kalkan" hakkı var, şu an etkin mi.
  int get shieldCharges => _profile.shieldCharges.value;
  bool get shieldActive => _game.shieldActive.value;
  bool get canUseShield => shieldCharges > 0 && !shieldActive;

  /// Dil seçimi: bütün diller ve şu an seçili olan.
  List<AppLanguage> get languages => AppLanguage.values;
  AppLanguage get language => _profile.language.value;

  LevelTileState tileState(int index) {
    if (index >= levels.length) return LevelTileState.soon;
    if (_profile.isPlayable(index)) return LevelTileState.current;
    if (_profile.isCompleted(index)) return LevelTileState.done;
    return LevelTileState.locked;
  }

  /// [index]'ten bir sonrakine giden boru yanıyor mu (bölüm bitirildiyse).
  bool isPathLit(int index) => _profile.isCompleted(index);

  // --- Aksiyonlar --------------------------------------------------------------

  void showLevels() => _setPage(MenuPage.levels);
  void showShop() => _setPage(MenuPage.shop);
  void showHome() => _setPage(MenuPage.home);
  void showLanguages() => _setPage(MenuPage.language);

  /// Dil değişince bütün yazılar yeni dilde yeniden çizilir; ana sayfaya dönülür.
  Future<void> setLanguage(AppLanguage value) async {
    _page = MenuPage.home;
    await _profile.setLanguage(value);
  }

  void _setPage(MenuPage page) {
    if (_page == page) return;
    _page = page;
    notifyListeners();
  }

  /// Ana sayfada ekranı kaydırınca: arkadaki bölümü oynat.
  void playSwipedLevel() => _game.playMenuLevel();

  /// "Yeni Oyun": ilerleme sıfırlanır, 1. bölüm başlar.
  void newGame() => _game.newGame();

  /// Haritada bir kareye dokunuldu (oynanamıyorsa bir şey olmaz).
  void playLevel(int index) {
    if (tileState(index) == LevelTileState.current) _game.startLevel(index);
  }

  void toggleMusic() => _game.toggleMusic();

  /// Oyun içinde ayna butonu: lideri 4 saniye kör et.
  void useBlind() => _game.useBlind();

  /// Oyunda kalkan butonu: 15 sn rakiplerin saldırılarına karşı koru.
  void useShield() => _game.useShield();

  /// Oyun içi menü: açılınca oyun durur, kapanınca devam eder.
  void pauseGame() => _game.pauseEngine();
  void resumeGame() => _game.resumeEngine();

  /// Oyundan ana menüye dön (menü ana sayfadan açılır).
  void backToMenu() {
    _page = MenuPage.home;
    _game.backToMenu();
  }

  @override
  void dispose() {
    _profile.completedLevels.removeListener(notifyListeners);
    _profile.musicOn.removeListener(notifyListeners);
    _profile.coins.removeListener(notifyListeners);
    _game.menuLevel.removeListener(notifyListeners);
    _profile.blindCharges.removeListener(notifyListeners);
    _game.blindActive.removeListener(notifyListeners);
    _profile.shieldCharges.removeListener(notifyListeners);
    _game.shieldActive.removeListener(notifyListeners);
    _profile.language.removeListener(notifyListeners);
    super.dispose();
  }
}
