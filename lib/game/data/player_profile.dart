import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../l10n/strings.dart';

/// Oyuncunun kalıcı bilgileri (Model): bölüm ilerlemesi, en son oynanan
/// bölüm, ayarlar, altın ve mağazadan alınanlar. Telefona kaydetme ve okuma
/// yalnızca burada yapılır.
///
/// Arayüz [completedLevels], [musicOn], [coins], [extraLives],
/// [blindCharges] ve [shieldCharges]'ı dinler;
/// oyun kuralları ise [isPlayable], [currentLevel], [maxLives] gibi
/// sorgularla kuralları öğrenir.
class PlayerProfile {
  PlayerProfile({required this.levelCount});

  final int levelCount;

  static const String _completedKey = 'completedLevels';
  static const String _legacyUnlockedKey =
      'unlockedLevels'; // eski kayıt: açık bölüm sayısı
  static const String _lastLevelKey = 'lastLevel';
  static const String _musicKey = 'musicOn';
  static const String _coinsKey = 'coins';
  static const String _extraLivesKey = 'extraLives';
  static const String _blindChargesKey = 'blindCharges';
  static const String _shieldChargesKey = 'shieldCharges';
  static const String _languageKey = 'language';

  static const int baseLives = 2;

  SharedPreferences? _prefs;

  /// Kaç bölüm bitirildi.
  ///
  /// İlerleme tek yönlü: yalnızca sıradaki bölüm oynanır, bitirilen bölüme
  /// dönülmez. Bütün bölümler bitince hepsi serbestçe oynanabilir.
  final ValueNotifier<int> completedLevels = ValueNotifier(0);

  final ValueNotifier<bool> musicOn = ValueNotifier(true);

  /// En son başlatılan bölüm (menünün arkasındaki sahne); kayıt yoksa null.
  int? lastLevel;

  /// Altın: bölüm bitirince kazanılır, mağazada harcanır.
  final ValueNotifier<int> coins = ValueNotifier(0);

  /// Mağazadan alınmış ek canlar (kalıcı).
  final ValueNotifier<int> extraLives = ValueNotifier(0);

  /// Mağazadan alınmış "Kör Et" hakları (oyunda kullanınca biri gider).
  final ValueNotifier<int> blindCharges = ValueNotifier(0);

  /// Mağazadan alınmış "Kalkan" hakları (oyunda kullanınca biri gider).
  final ValueNotifier<int> shieldCharges = ValueNotifier(0);

  /// Oyunun dili. Kayıt yoksa cihazın dili (desteklenmiyorsa İngilizce).
  final ValueNotifier<AppLanguage> language = ValueNotifier(AppLanguage.en);

  /// Bölüm başına can.
  int get maxLives => baseLives + extraLives.value;

  bool get allCompleted => completedLevels.value >= levelCount;

  /// Sıradaki (oynanacak) bölüm; hepsi bittiyse ilk bölüm.
  int get currentLevel => allCompleted ? 0 : completedLevels.value;

  /// tüm bölümlere bakmak için:    index < levelCount && (true || allCompleted || index == completedLevels.value);
  bool isPlayable(int index) =>
      index < levelCount && (allCompleted || index == completedLevels.value);

  bool isCompleted(int index) => index < completedLevels.value;

  /// Kayıtlı bilgileri okur (oyun açılırken bir kez).
  Future<void> load() async {
    final prefs = _prefs = await SharedPreferences.getInstance();
    completedLevels.value =
        (prefs.getInt(_completedKey) ??
                (prefs.getInt(_legacyUnlockedKey) ?? 1) - 1)
            .clamp(0, levelCount);
    lastLevel = prefs.getInt(_lastLevelKey)?.clamp(0, levelCount - 1);
    musicOn.value = prefs.getBool(_musicKey) ?? true;
    coins.value = prefs.getInt(_coinsKey) ?? 0;
    extraLives.value = prefs.getInt(_extraLivesKey) ?? 0;
    blindCharges.value = prefs.getInt(_blindChargesKey) ?? 0;
    shieldCharges.value = prefs.getInt(_shieldChargesKey) ?? 0;
    language.value = AppLanguage.fromCode(
      prefs.getString(_languageKey) ??
          PlatformDispatcher.instance.locale.languageCode,
    );
    L.language = language.value;
  }

  Future<void> setLanguage(AppLanguage value) async {
    L.language = value;
    language.value = value;
    await (await _store).setString(_languageKey, value.name);
  }

  Future<SharedPreferences> get _store async =>
      _prefs ??= await SharedPreferences.getInstance();

  /// Bölüm bitti: sıradaki bölüm açılır, bu bölüm kapanır.
  Future<void> completeLevel(int index) async {
    final completed = index + 1;
    if (completed <= completedLevels.value) return;
    completedLevels.value = completed;
    await (await _store).setInt(_completedKey, completed);
  }

  /// "Yeni Oyun": ilerleme sıfırlanır.
  Future<void> resetProgress() async {
    completedLevels.value = 0;
    await (await _store).setInt(_completedKey, 0);
  }

  Future<void> setLastLevel(int index) async {
    lastLevel = index;
    await (await _store).setInt(_lastLevelKey, index);
  }

  Future<void> setMusicOn(bool on) async {
    musicOn.value = on;
    await (await _store).setBool(_musicKey, on);
  }

  Future<void> addCoins(int amount) async {
    coins.value += amount;
    await (await _store).setInt(_coinsKey, coins.value);
  }

  /// Yeterli altın varsa harcar ve true döner; yoksa hiçbir şey değişmez.
  Future<bool> spendCoins(int amount) async {
    if (amount > coins.value) return false;
    coins.value -= amount;
    await (await _store).setInt(_coinsKey, coins.value);
    return true;
  }

  Future<void> addExtraLife() async {
    extraLives.value++;
    await (await _store).setInt(_extraLivesKey, extraLives.value);
  }

  Future<void> addBlindCharge() async {
    blindCharges.value++;
    await (await _store).setInt(_blindChargesKey, blindCharges.value);
  }

  /// Bir "Kör Et" hakkı harcar; hakkı yoksa false döner.
  bool useBlindCharge() {
    if (blindCharges.value <= 0) return false;
    blindCharges.value--;
    _store.then((prefs) => prefs.setInt(_blindChargesKey, blindCharges.value));
    return true;
  }

  Future<void> addShieldCharge() async {
    shieldCharges.value++;
    await (await _store).setInt(_shieldChargesKey, shieldCharges.value);
  }

  /// Bir "Kalkan" hakkı harcar; hakkı yoksa false döner.
  bool useShieldCharge() {
    if (shieldCharges.value <= 0) return false;
    shieldCharges.value--;
    _store.then(
      (prefs) => prefs.setInt(_shieldChargesKey, shieldCharges.value),
    );
    return true;
  }
}
