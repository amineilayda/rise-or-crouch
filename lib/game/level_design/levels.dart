import 'dart:math';
import 'dart:ui';

import '../l10n/strings.dart';

/// Bir nokta ışığı: oyun koordinatlarında konum, renk ve şiddet.
typedef PointLightSpec = ({
  double x,
  double y,
  double z,
  Color color,
  double intensity,
});

/// Bir bölümün zorluk ayarları ve görünümü.
class LevelConfig {
  const LevelConfig({
    required this.number,
    required this.duration,
    required this.commandInterval,
    required this.reactionTime,
    required this.trickChance,
    required this.repeatChance,
    required this.eliminations,
    required this.environmentModel,
    required this.skyTop,
    required this.skyHorizon,
    required this.sunAndClouds,
    required this.ground,
    required this.ambientColor,
    required this.ambientIntensity,
    required this.lights,
    this.snow = false,
    this.leaderModel = 'models/leaders/rogue.glb',
    this.freezeChance = 0,
    this.reverseControls = false,
    this.enemyBlind = false,
    this.rivalTaunts = false,
    this.doubleChance = 0,
    this.lastOneStanding = false,
  });

  final int number;

  /// Bölümün adı, oyuncunun dilinde (l10n/strings.dart: level{n}).
  String get name => L.levelName(number);

  /// Bölümün süresi (saniye).
  final double duration;

  /// İki komut arasındaki ortalama süre (saniye).
  final double commandInterval;

  /// Komuttan sonra doğru pozisyona geçmek için tanınan süre (saniye).
  final double reactionTime;

  /// Oyun kurucunun söylediğinin tersini yaparak kandırma olasılığı.
  final double trickChance;

  /// Aynı komutun üst üste tekrar edilme olasılığı.
  final double repeatChance;

  /// Bölümde kaç NPC'nin yanacağı (en az, en çok). Yanmalar bölüm süresine
  /// yayılır; böylece süre ne olursa olsun (test süresi dahil) mutlaka olur.
  /// Sırada en az bir NPC kalacak kadarıyla sınırlanır ([lastOneStanding]
  /// hariç). 1–3. bölümlerde kimse yanmaz; 4–8'de toplam 3–4 kişi yanar, son
  /// bölüme 1–2 rakiple girilir (bkz. [eliminatedBefore]).
  final (int, int) eliminations;

  /// Son bölüm: sırada kalan herkes sürenin bitiminden önce yanar; oyuncu
  /// tek başına kalınca bölüm (ve oyun) kazanılmış biter.
  final bool lastOneStanding;

  /// Ortam modeli (tools/export_scene.py ile üretilir).
  final String environmentModel;

  final Color skyTop;
  final Color skyHorizon;
  final bool sunAndClouds;

  final Color ground;

  final Color ambientColor;
  final double ambientIntensity;

  /// En fazla 8 nokta ışığı (flame_3d sınırı).
  final List<PointLightSpec> lights;

  /// Ekranda kar yağsın mı.
  final bool snow;

  /// Oyun kurucunun modeli (bölüme göre kıyafeti değişir).
  final String leaderModel;

  /// Şaşırtma: bir komutun yerine ekranın ortasında "SABİT KAL!" çıkma
  /// olasılığı. O sırada kaydıran oyuncu yanar.
  final double freezeChance;

  /// Bölümde arada bir kontroller tersine döner: yukarı kaydırmak CÜCE,
  /// aşağı kaydırmak DEVE olur. Ekranda uyarı şeridi çıkar.
  final bool reverseControls;

  /// Rakipler arada bir oyuncuyu kör eder: ekran birkaç saniye bulanıklaşır.
  final bool enemyBlind;

  /// Rakipler arada bir "dayanamazsın" diye laf sokar (yalnızca dikkat dağıtır).
  final bool rivalTaunts;

  /// Çift komut olasılığı: lider iki komutu art arda söyler ("DEVE, CÜCE!");
  /// oyuncu ikisini de sırayla yapmalı.
  final double doubleChance;

  /// Bölüm başında gösterilen, o bölümde gelen yeni kuralı anlatan ipucu
  /// (l10n/strings.dart: tip{n}; yoksa null).
  String? get tip => L.levelTip(number);
}

const List<LevelConfig> levels = [
  LevelConfig(
    number: 1,
    duration: 150,
    commandInterval: 3.0,
    reactionTime: 1.6,
    trickChance: 0.0,
    repeatChance: 0.20,
    eliminations: (0, 0),
    environmentModel: 'models/levels/level_1.glb',
    skyTop: Color(0xFF3E9BE6),
    skyHorizon: Color(0xFFCFEFFF),
    sunAndClouds: true,
    ground: Color(0xFF7CC850),
    ambientColor: Color(0xFFE6EEFF),
    ambientIntensity: 1.3,
    lights: [
      // Sıcak ana ışık (güneş), soğuk dolgu, kenarları parlatan arka ışık.
      (x: 8, y: 14, z: 12, color: Color(0xFFFFE2B8), intensity: 500),
      (x: -10, y: 6, z: 4, color: Color(0xFFB8D4FF), intensity: 120),
      (x: 0, y: 8, z: -16, color: Color(0xFFFFF4E0), intensity: 250),
    ],
  ),
  LevelConfig(
    number: 2,
    duration: 210,
    commandInterval: 1.9,
    reactionTime: 1.0,
    trickChance: 0.0,
    repeatChance: 0.35,
    eliminations: (0, 0),
    environmentModel: 'models/levels/level_2.glb',
    skyTop: Color(0xFF0B0908),
    skyHorizon: Color(0xFF1E1814),
    sunAndClouds: false,
    ground: Color(0xFF2E2A26),
    ambientColor: Color(0xFFB89A7A),
    ambientIntensity: 0.55,
    lights: [
      // Karakterleri aydınlatan, kameranın arkasından gelen sıcak ışık.
      (x: 3, y: 6, z: 5, color: Color(0xFFFFE0C0), intensity: 160),
      // Meşaleler (tools/build_dungeon.py'deki konumlarla aynı).
      (x: -9.6, y: 2.4, z: -7, color: Color(0xFFFF9A40), intensity: 60),
      (x: 9.6, y: 2.4, z: -7, color: Color(0xFFFF9A40), intensity: 60),
      (x: -9.6, y: 2.4, z: -15, color: Color(0xFFFF9A40), intensity: 60),
      (x: 9.6, y: 2.4, z: -15, color: Color(0xFFFF9A40), intensity: 60),
      (x: -2.5, y: 2.4, z: -31.5, color: Color(0xFFFF9A40), intensity: 120),
      (x: 2.5, y: 2.4, z: -31.5, color: Color(0xFFFF9A40), intensity: 120),
    ],
    // Kahverengi deri, zindana uygun kıyafet (tools/make_rogue_outfit.py, tema: dungeon).
    leaderModel: 'models/leaders/rogue_dungeon.glb',
  ),
  LevelConfig(
    number: 3,
    duration: 240,
    // Hızlı bölüm: komutlar sık, tepki süresi kısa.
    commandInterval: 1.4,
    reactionTime: 0.85,
    trickChance: 0.10,
    // Kandırma ilk kez bu bölümde geliyor.
    repeatChance: 0.35,
    eliminations: (0, 0),
    environmentModel: 'models/levels/level_3.glb',
    // Kapalı kış göğü: bulut ve güneş yok, kar yağıyor.
    skyTop: Color(0xFF9FB8D0),
    skyHorizon: Color(0xFFE8EFF6),
    sunAndClouds: false,
    snow: true,
    ground: Color(0xFFEEF4FA),
    ambientColor: Color(0xFFDCE8FF),
    ambientIntensity: 1.4,
    lights: [
      // Soğuk beyaz ana ışık, mavi dolgu, arka ışık.
      (x: 8, y: 14, z: 12, color: Color(0xFFF0F6FF), intensity: 450),
      (x: -10, y: 6, z: 4, color: Color(0xFFC8DCFF), intensity: 140),
      (x: 0, y: 8, z: -16, color: Color(0xFFDDEBFF), intensity: 220),
    ],
    // Soluk mavi, kar temalı kıyafet (tools/make_rogue_outfit.py, tema: snow).
    leaderModel: 'models/leaders/rogue_snow.glb',
  ),
  LevelConfig(
    number: 4,
    duration: 240,
    // En hızlı bölüm; üstüne "SABİT KAL!" şaşırtması geliyor.
    commandInterval: 1.15,
    reactionTime: 0.75,
    trickChance: 0.12,
    repeatChance: 0.35,
    freezeChance: 0.18,
    reverseControls: true,
    eliminations: (1, 1),
    environmentModel: 'models/levels/level_4.glb',
    // Güneşli tropik gök.
    skyTop: Color(0xFF2F9BE6),
    skyHorizon: Color(0xFFCDEFFF),
    sunAndClouds: true,
    ground: Color(0xFFE8D29A),
    ambientColor: Color(0xFFFFF2DC),
    ambientIntensity: 1.3,
    lights: [
      // Sıcak tropik güneş, deniz yansıması gibi mavi dolgu, arka ışık.
      (x: 8, y: 14, z: 12, color: Color(0xFFFFE6C0), intensity: 520),
      (x: -10, y: 6, z: 4, color: Color(0xFFBFE4FF), intensity: 130),
      (x: 0, y: 8, z: -16, color: Color(0xFFFFF0D8), intensity: 240),
    ],
    // Kırmızı korsan ceketi ve göz bandı (tools/make_rogue_outfit.py, tema: pirate).
    leaderModel: 'models/leaders/rogue_pirate.glb',
  ),
  LevelConfig(
    number: 5,
    duration: 240,
    // 4. bölüm kadar hızlı; ters kontrol yerine rakipler kör eder.
    commandInterval: 1.15,
    reactionTime: 0.8,
    trickChance: 0.12,
    repeatChance: 0.35,
    freezeChance: 0.12,
    enemyBlind: true,
    eliminations: (0, 1),
    environmentModel: 'models/levels/level_5.glb',
    // Mor gece göğü; bulut ve güneş yok.
    skyTop: Color(0xFF120A22),
    skyHorizon: Color(0xFF4A2A5E),
    sunAndClouds: false,
    ground: Color(0xFF3A3240),
    ambientColor: Color(0xFFB8B0FF),
    ambientIntensity: 0.75,
    lights: [
      // Soğuk ay ışığı ve karakterleri aydınlatan yumuşak ışık.
      (x: 8, y: 14, z: 12, color: Color(0xFFC8C8FF), intensity: 380),
      (x: 3, y: 6, z: 5, color: Color(0xFFE0D8FF), intensity: 120),
      // Oyma balkabaklarının turuncu ışığı (build_halloween.py konumları).
      (x: -2.4, y: 1.2, z: -9.3, color: Color(0xFFFF8A2A), intensity: 45),
      (x: 2.5, y: 1.2, z: -9.4, color: Color(0xFFFF8A2A), intensity: 45),
      // Mahzenin önündeki fenerler.
      (x: -2.4, y: 1.4, z: -21.5, color: Color(0xFFFFB04A), intensity: 70),
      (x: 2.4, y: 1.4, z: -21.5, color: Color(0xFFFFB04A), intensity: 70),
    ],
  ),
  LevelConfig(
    number: 6,
    duration: 240,
    // Kurallar birleşir: ters kontrol ve körleme bir arada.
    commandInterval: 1.1,
    reactionTime: 0.75,
    trickChance: 0.15,
    repeatChance: 0.35,
    freezeChance: 0.15,
    reverseControls: true,
    enemyBlind: true,
    eliminations: (1, 1),
    environmentModel: 'models/levels/level_6.glb',
    // Akşam üstü şehir göğü.
    skyTop: Color(0xFF4A5FA8),
    skyHorizon: Color(0xFFF6B27A),
    sunAndClouds: true,
    ground: Color(0xFFB9B2A6),
    ambientColor: Color(0xFFFFE6D0),
    ambientIntensity: 1.2,
    lights: [
      // Alçak turuncu akşam güneşi, soğuk dolgu, arka ışık.
      (x: 8, y: 14, z: 12, color: Color(0xFFFFD2A0), intensity: 480),
      (x: -10, y: 6, z: 4, color: Color(0xFFB8C8FF), intensity: 130),
      (x: 0, y: 8, z: -16, color: Color(0xFFFFE4C8), intensity: 230),
      // Caddenin iki yanındaki sokak lambaları (tools/build_city.py konumları).
      (x: -11, y: 3.2, z: -10.1, color: Color(0xFFFFD890), intensity: 50),
      (x: 11, y: 3.2, z: -10.1, color: Color(0xFFFFD890), intensity: 50),
    ],
  ),
  LevelConfig(
    number: 7,
    duration: 240,
    // Rakipler sürekli laf sokar; ters kontrol ve SABİT KAL! de sürer.
    commandInterval: 1.08,
    reactionTime: 0.74,
    trickChance: 0.15,
    repeatChance: 0.35,
    freezeChance: 0.15,
    reverseControls: true,
    rivalTaunts: true,
    eliminations: (0, 1),
    environmentModel: 'models/levels/level_7.glb',
    // İç mekân: tavanın karanlığı.
    skyTop: Color(0xFF1E1410),
    skyHorizon: Color(0xFF3A2A22),
    sunAndClouds: false,
    ground: Color(0xFF8A6A52),
    ambientColor: Color(0xFFFFE8D0),
    ambientIntensity: 1.1,
    lights: [
      // Sıcak tavan ışığı ve kameranın arkasından dolgu.
      (x: 0, y: 7, z: 2, color: Color(0xFFFFE2B8), intensity: 420),
      (x: 3, y: 6, z: 5, color: Color(0xFFFFF0DC), intensity: 140),
      // Davlumbaz ışıkları (tools/build_restaurant.py'deki ocakların üstü).
      (x: -6, y: 2.6, z: -10.5, color: Color(0xFFFFD08A), intensity: 45),
      (x: 0, y: 2.6, z: -10.5, color: Color(0xFFFFD08A), intensity: 45),
      (x: 4, y: 2.6, z: -10.5, color: Color(0xFFFFD08A), intensity: 45),
    ],
  ),
  LevelConfig(
    number: 8,
    duration: 240,
    // Yeni kural çift komut; dikkat ona kalsın diye eski kurallardan
    // yalnızca hafif bir kandırma var.
    commandInterval: 1.08,
    reactionTime: 0.75,
    trickChance: 0.08,
    repeatChance: 0.3,
    doubleChance: 0.3,
    eliminations: (1, 1),
    environmentModel: 'models/levels/level_8.glb',
    // İç mekân: karanlık fabrika tavanı.
    skyTop: Color(0xFF14161A),
    skyHorizon: Color(0xFF2A2E34),
    sunAndClouds: false,
    ground: Color(0xFF5E6266),
    ambientColor: Color(0xFFE4ECFF),
    ambientIntensity: 1.15,
    lights: [
      // Soğuk beyaz tavan lambaları ve kameranın arkasından dolgu.
      (x: -4, y: 7, z: -6, color: Color(0xFFE8F0FF), intensity: 300),
      (x: 4, y: 7, z: -6, color: Color(0xFFE8F0FF), intensity: 300),
      (x: 3, y: 6, z: 5, color: Color(0xFFF4F6FF), intensity: 140),
      // Bandın üstünde sarı uyarı ışığı.
      (x: 0, y: 3.5, z: -11, color: Color(0xFFFFC24A), intensity: 60),
    ],
  ),
  LevelConfig(
    number: 9,
    duration: 240,
    // Final: önceki kuralların çoğu bir arada ama hepsi seyrek; komutların
    // yarısından fazlası yine düz DEVE / CÜCE. Ters kontrol yok (tek başına
    // sürenin ~%40'ını kaplıyor).
    commandInterval: 1.05,
    reactionTime: 0.72,
    trickChance: 0.08,
    repeatChance: 0.35,
    freezeChance: 0.08,
    enemyBlind: true,
    rivalTaunts: true,
    doubleChance: 0.12,
    eliminations: (0, 0),
    // Sırada kalan herkes elenir; tek başına kalınca kazanılır.
    lastOneStanding: true,
    environmentModel: 'models/levels/level_9.glb',
    // Açık yaz göğü.
    skyTop: Color(0xFF3C8FE0),
    skyHorizon: Color(0xFFD2ECFF),
    sunAndClouds: true,
    ground: Color(0xFF6FA84A),
    ambientColor: Color(0xFFEAF0FF),
    ambientIntensity: 1.3,
    lights: [
      // Sıcak güneş, soğuk dolgu, arka ışık.
      (x: 8, y: 14, z: 12, color: Color(0xFFFFE6C4), intensity: 500),
      (x: -10, y: 6, z: 4, color: Color(0xFFBCD4FF), intensity: 120),
      (x: 0, y: 8, z: -16, color: Color(0xFFFFF2E0), intensity: 250),
    ],
  ),
];

/// [index]. bölüm başlarken, önceki bölümlerde sıradan kaç kişinin (en az,
/// en çok) çoktan yanmış olacağı. Sırada en az bir kişi kalır.
(int, int) eliminatedBefore(int index, {required int npcCount}) {
  var low = 0;
  var high = 0;
  for (final level in levels.take(index)) {
    low = min(low + level.eliminations.$1, npcCount - 1);
    high = min(high + level.eliminations.$2, npcCount - 1);
  }
  return (low, high);
}
