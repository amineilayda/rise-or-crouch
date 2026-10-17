import 'dart:math';
import 'dart:ui' as ui;

import 'package:flame/cache.dart';
import 'package:flame/events.dart';
import 'package:flame_audio/flame_audio.dart';
import 'package:flame_3d/camera.dart';
import 'package:flame_3d/components.dart';
import 'package:flame_3d/game.dart';
import 'package:flame_3d/model.dart';
import 'package:flame_3d/parser.dart';
import 'package:flame_3d/resources.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart' show KeyEventResult, ValueNotifier;

import '../data/characters.dart';
import '../data/player_profile.dart';
import '../l10n/strings.dart';
import '../level_design/gate.dart';
import '../level_design/levels.dart';
import '../level_design/sky.dart';
import '../level_design/snowfall.dart';
import 'character.dart';
import 'hud.dart';
import 'pose.dart';
import 'stage_camera.dart';

enum GamePhase { menu, intro, playing, gameOver, levelComplete }

/// Rise or Crouch: 6 kişilik sıra (3 solda, oyuncu, 2 sağda), karşıda oyun kurucu.
///
/// Akış: menü → "Devam Et" / "Yeni Oyun" → kamera iner → oyun kurucu DEVE / CÜCE der →
/// oyuncu yukarı/aşağı kaydırır. Yanlış yöne kaydırırsa ya da
/// tepki süresi içinde doğru pozisyona geçmezse yanar.
class RiseCrouchGame extends FlameGame3D<World3D, StageCamera>
    with DragCallbacks, KeyboardEvents {
  RiseCrouchGame()
    : super(
        world: World3D(),
        camera: StageCamera(
          playerX: _slotX(playerSlot),
          lookAt: Vector3(0, 1.8, leaderZ),
        ),
      );

  static const String overlayMenu = 'menu';
  static const String overlayGameOver = 'gameOver';
  static const String overlayLevelComplete = 'levelComplete';
  static const String overlayFinished = 'finished';
  static const String overlayOptions = 'options';
  static const String overlayBlinded = 'blinded';

  static const int rowSize = 6;
  static const int playerSlot = 3;
  static const double spacing = 1.45;
  static const double leaderZ = -7;

  static double _slotX(int i) => (i - (rowSize - 1) / 2) * spacing;

  /// Sıradaki yerin portre / model numarası (oyuncu atlanır; 0'dan başlar).
  static int _portraitIndex(int slot) => slot < playerSlot ? slot : slot - 1;

  final Random _random = Random();
  final Hud _hud = Hud();

  /// Oyun kurucu; bölüme göre kıyafeti farklı modeller arasında değişir.
  /// Hepsi sahnede durur, yalnızca o bölümünki görünür.
  late Character _leader;
  final Map<String, Character> _leaders = {};
  late final Character _player;
  final List<Character> _npcs = [];
  final Map<Character, int> _slotOf = {};

  /// Hata yapan NPC'lerin yanacağı an: (kalan süre, NPC).
  final List<(double, Character)> _pendingEliminations = [];

  /// Bu bölümde NPC'lerin yanacağı anlar (bölümde geçen süre, sıralı).
  final List<double> _eliminationTimes = [];

  /// Önceki bölümlerde yanıp bu oyunda artık sırada olmayanların yerleri.
  /// Yeni oyunda / menüde sıfırlanır; aynı bölümü tekrar oynayınca korunur.
  final Set<int> _outSlots = {};

  GamePhase phase = GamePhase.menu;
  String loseReason = '';

  int levelIndex = 0;
  LevelConfig get level => levels[levelIndex];
  bool get isLastLevel => levelIndex == levels.length - 1;

  double get levelDuration => level.duration;

  /// Kalıcı oyuncu bilgileri: ilerleme, son bölüm, ayarlar (kayıt orada).
  final PlayerProfile profile = PlayerProfile(levelCount: levels.length);

  /// Menünün arkasındaki sahnenin bölümü; menüde kaydırınca bu bölüm başlar.
  /// En son oynanan bölümdür; o artık oynanamıyorsa sıradaki bölüm.
  final ValueNotifier<int> menuLevel = ValueNotifier(0);

  /// "Kör Et": ayna ile lider [blindDuration] saniye kör olur; bu sürede
  /// hatalar can götürmez. Oyun içi buton [blindActive]'i dinler.
  static const double blindDuration = 4;
  final ValueNotifier<bool> blindActive = ValueNotifier(false);
  double _blindLeft = 0;

  /// Oyun içi ayna butonu: hak varsa ve oyun sürüyorsa lideri kör eder.
  bool useBlind() {
    if (phase != GamePhase.playing || paused || _blindLeft > 0) return false;
    if (!profile.useBlindCharge()) return false;
    _blindLeft = blindDuration;
    blindActive.value = true;
    _hud
      ..blindLeft = _blindLeft
      ..flash(Hud.freezeColor, alpha: 0.35);
    return true;
  }

  /// "Kalkan": [shieldDuration] saniye boyunca rakiplerin saldırıları
  /// (körleme, ters kontrol, laf sokma) işlemez. Liderin kendi şaşırtmaları
  /// (kandırma, SABİT KAL!) etkilenmez. Oyun içi buton [shieldActive]'i dinler.
  static const double shieldDuration = 15;
  final ValueNotifier<bool> shieldActive = ValueNotifier(false);
  double _shieldLeft = 0;

  /// Oyun içi kalkan butonu: hak varsa ve oyun sürüyorsa kalkanı açar. O an
  /// süren bir körleme ya da ters kontrol varsa hemen kalkar.
  bool useShield() {
    if (phase != GamePhase.playing || paused || _shieldLeft > 0) return false;
    if (!profile.useShieldCharge()) return false;
    _shieldLeft = shieldDuration;
    shieldActive.value = true;
    _hud
      ..shieldLeft = _shieldLeft
      ..flash(Hud.shieldColor, alpha: 0.35);
    if (_blindedLeft > 0) _endEnemyBlind();
    if (_reversed) {
      _reversed = false;
      _nextReverseToggle = _levelTime + _randomIn(_normalPhase);
      _hud
        ..reversed = false
        ..showText(L.controlsNormal, color: Hud.deveColor);
    }
    return true;
  }

  void _updateShield(double dt) {
    if (_shieldLeft <= 0) return;
    _shieldLeft -= dt;
    _hud.shieldLeft = max(0, _shieldLeft);
    if (_shieldLeft <= 0) _endShield();
  }

  void _endShield() {
    _shieldLeft = 0;
    shieldActive.value = false;
    _hud.shieldLeft = 0;
  }

  bool get _shielded => _shieldLeft > 0;

  /// Rakiplerin "kör etme"si (5. bölüm): sıradakilerden biri laf sokar,
  /// [_enemyBlindLead] sn sonra ekran [enemyBlindDuration] sn bulanıklaşır.
  /// Bulanıklık arayüzde [overlayBlinded] ile çizilir; kimin yaptığı
  /// [blindedByName]'de.
  static const double enemyBlindDuration = 3;
  static const double _enemyBlindLead = 0.6;
  static const (double, double) _enemyBlindGap = (8, 13);
  double _blindedLeft = 0;
  double _nextEnemyBlind = 0;
  String blindedByName = '';

  void _updateEnemyBlind(double dt) {
    if (_blindedLeft > 0) {
      _blindedLeft -= dt;
      if (_blindedLeft <= 0) {
        _endEnemyBlind();
      } else if (_blindedLeft <= enemyBlindDuration) {
        overlays.add(overlayBlinded); // laf sokma görüldükten sonra bulanıklaş
      }
      return;
    }
    if (!level.enemyBlind ||
        _levelTime < _nextEnemyBlind ||
        _deadline != null ||
        _freezing) {
      return;
    }
    final alive = _npcs.where((npc) => !npc.eliminated).toList();
    if (alive.isEmpty) return;
    if (_shielded) {
      _nextEnemyBlind = _levelTime + _randomIn(_enemyBlindGap);
      _hud.toast(L.shieldBlocked, color: Hud.shieldColor);
      return;
    }
    final caster = alive[_random.nextInt(alive.length)];
    final index = _portraitIndex(_slotOf[caster]!);
    blindedByName = characterNames[index];
    _blindedLeft = _enemyBlindLead + enemyBlindDuration;
    _nextEnemyBlind = _levelTime + _blindedLeft + _randomIn(_enemyBlindGap);
    _hud
      ..taunt(index, L.taunt(1 + _random.nextInt(L.tauntCount)))
      ..toast(L.blindedBy(blindedByName), color: Hud.reverseColor)
      ..flash(const Color(0xFF3A1A5A), alpha: 0.4);
  }

  /// 7. bölüm: sıradakilerden biri arada bir "dayanamazsın" diye laf sokar.
  /// Kural değiştirmez; yalnızca dikkat dağıtır. Başka bir balonun üstüne
  /// binmez; ilki bölüm ipucu kapandıktan sonra gelir.
  static const (double, double) _rivalTauntGap = (4, 7);
  static const double _firstRivalTaunt = 6;
  double _nextRivalTaunt = 0;

  void _updateRivalTaunts() {
    if (!level.rivalTaunts || _levelTime < _nextRivalTaunt) return;
    if (_blindedLeft > 0 || _hud.tauntShowing || _shielded) return;
    final alive = _npcs.where((npc) => !npc.eliminated).toList();
    if (alive.isEmpty) return;
    final rival = alive[_random.nextInt(alive.length)];
    _hud.taunt(
      _portraitIndex(_slotOf[rival]!),
      L.endureTaunt(1 + _random.nextInt(L.endureTauntCount)),
    );
    _nextRivalTaunt = _levelTime + _randomIn(_rivalTauntGap);
  }

  void _endEnemyBlind() {
    _blindedLeft = 0;
    overlays.remove(overlayBlinded);
  }

  void _endBlind() {
    _blindLeft = 0;
    blindActive.value = false;
    _hud.blindLeft = 0;
  }

  void _pickMenuLevel() {
    if (!profile.isPlayable(levelIndex)) levelIndex = profile.currentLevel;
    menuLevel.value = levelIndex;
  }

  /// Menüde ekranı kaydırınca: arkadaki bölümü oynat.
  void playMenuLevel() => startLevel(menuLevel.value);

  static const String _musicFile = 'music.wav';

  /// Biri yanınca çalan "daat" sesi.
  static const String _buzzerFile = 'buzzer.mp3';
  bool _musicStarted = false;
  bool _musicLoading = false;

  /// Bölümde geçen süre (kamera yanan birini izlerken durur).
  double _levelTime = 0;
  double _levelCompleteDelay = 0;

  // Bölüme göre değişen sahne parçaları.
  final List<ModelComponent> _environments = [];
  final List<List<LightComponent>> _levelLights = [];
  late final SpatialMaterial _groundMaterial;
  final Sky _sky = Sky();
  final Snowfall _snowfall = Snowfall();
  int? _appliedLevel;

  /// "SABİT KAL!" şaşırtması sürüyor mu (o sırada kaydıran yanar).
  bool _freezing = false;

  /// Bölümde kalan can. Hata bir can götürür; son can da gidince yanılır.
  /// Başlangıç sayısı profilden gelir (ileride mağazadan artırılabilecek).
  int _lives = 0;

  /// Kontroller ters mi (yukarı = CÜCE). Ters dönemleri bölüm süresinde
  /// belli aralıklarla gelir; yalnızca oyuncu doğru pozdayken başlar/biter.
  bool _reversed = false;
  double _nextReverseToggle = 0;
  static const double _reversePhase = 8; // ters kalınan süre (sn)
  static const (double, double) _normalPhase = (
    9,
    14,
  ); // iki ters dönem arası (sn)
  Pose _required = Pose.stand;
  Pose _playerPose = Pose.stand;

  /// Çift komutun ikinci yarısı: oyuncu [_required]'ı yapınca istenecek poz.
  Pose? _comboNext;

  /// Çift komutta liderin ve sıradakilerin ikinci hareketi gibi, birkaç
  /// saniye sonra yapılacak işler: (kalan süre, iş).
  final List<(double, void Function())> _later = [];
  double? _deadline;
  double _untilCommand = 0;
  double _gameOverDelay = 0;
  double _dragDy = 0;

  @override
  Color backgroundColor() => const Color(0xFF8FD3F4);

  @override
  Future<void> onLoad() async {
    await profile.load();
    levelIndex = profile.lastLevel ?? profile.currentLevel;
    _pickMenuLevel();
    FlameAudio.bgm.initialize();
    _ensureMusic();

    // Sıradaki herkesin kendi karakteri var (portrelerle aynı sıra; oyuncu
    // ortadaki). tools/make_chibi.py + make_animations.py ile üretilir.
    final people = [
      for (var i = 1; i < rowSize; i++)
        await ModelParser.parse('models/people/player$i.glb'),
    ];
    final me = await ModelParser.parse('models/people/me.glb');
    // Ortamlar: tools/source_models/environment/level_N.blend'den
    // tools/export_scene.py ile üretilir. Koordinatları oyunla aynı.
    for (final config in levels) {
      _environments.add(
        ModelComponent(model: await ModelParser.parse(config.environmentModel)),
      );
      _levelLights.add(_lightsFor(config));
    }

    // Karakterler glTF'te +Z'ye bakıyor; sıra oyun kurucuya (-Z) dönsün.
    final faceLeader = Quaternion.axisAngle(Vector3(0, 1, 0), pi);

    for (var i = 0; i < rowSize; i++) {
      final character = Character(
        model: i == playerSlot ? me : people[_portraitIndex(i)],
        position: Vector3(_slotX(i), 0, 0),
        rotation: faceLeader,
      );
      if (i == playerSlot) {
        _player = character;
      } else {
        _npcs.add(character);
        _slotOf[character] = i;
      }
      world.add(character);
    }

    // Oyun kurucu: büyütülmüş Rogue (bölüme göre kıyafetiyle).
    for (final path in {for (final config in levels) config.leaderModel}) {
      _leaders[path] = Character(
        model: await ModelParser.parse(path),
        position: Vector3(0, 0, leaderZ),
        scale: Vector3.all(1.5),
      );
    }
    _leader = _leaders[level.leaderModel]!;

    // Yananların içine girip kaybolduğu iki kapı (tools/build_gate.py).
    final gateBody = await ModelParser.parse('models/props/gate.glb');
    final leftDoor = await ModelParser.parse('models/props/gate_door_left.glb');
    final rightDoor = await ModelParser.parse(
      'models/props/gate_door_right.glb',
    );
    _gates.addAll([
      for (final x in [-gateX, gateX])
        Gate(
          body: gateBody,
          leftDoor: leftDoor,
          rightDoor: rightDoor,
          position: Vector3(x, 0, leaderZ),
          rotation: _gateFacing(x),
        ),
    ]);

    _groundMaterial = _matte(level.ground);
    world.addAll([
      ..._leaders.values,
      MeshComponent(
        mesh: PlaneMesh(size: Vector2(200, 200), material: _groundMaterial),
      ),
      for (final gate in _gates) ...gate.parts,
    ]);

    // Portreler: player1..5, oyuncu hariç sıradaki yerlere soldan sağa.
    final portraitImages = Images(prefix: 'assets/images/portraits/');
    _hud
      ..portraits = [
        for (var i = 1; i < rowSize; i++)
          await portraitImages.load('player$i.png'),
      ]
      ..portraitNames = characterNames
      // Büyük resimler bellekte yer kaplamasın diye küçültülerek açılır.
      ..arrow = await _loadScaled('assets/images/icons/arrow.png', 256)
      ..heart = await _loadScaled('assets/images/icons/heart.png', 128);
    await FlameAudio.audioCache.load(_buzzerFile);

    // Gökyüzü 3D sahnenin arkasında çizilir (3D katmanın arkası şeffaf).
    add(_sky..priority = -1);
    camera.viewport.addAll([_snowfall..priority = -1, _hud]);
    _applyLevel();
  }

  /// Resmi [width] piksel genişliğe küçülterek açar.
  static Future<ui.Image> _loadScaled(String path, int width) async {
    final data = await rootBundle.load(path);
    final codec = await ui.instantiateImageCodec(
      data.buffer.asUint8List(),
      targetWidth: width,
    );
    return (await codec.getNextFrame()).image;
  }

  /// buzzer.mp3 ~1,8 sn; yalnızca başı çalınır.
  static const Duration _buzzerLength = Duration(milliseconds: 600);

  Future<void> _playBuzzer() async {
    const volume = 0.8;
    final player = await FlameAudio.play(_buzzerFile, volume: volume);
    await Future<void>.delayed(_buzzerLength);
    // Birden kesilince "tık" sesi çıkmasın diye kısa bir sönmeyle susar.
    for (var step = 4; step > 0; step--) {
      await player.setVolume(volume * step / 5);
      await Future<void>.delayed(const Duration(milliseconds: 25));
    }
    await player.dispose();
  }

  /// Bölümün ışıkları. Nokta ışıkları mesafenin karesiyle zayıfladığı için
  /// şiddetler büyük.
  static List<LightComponent> _lightsFor(LevelConfig config) => [
    LightComponent.ambient(
      color: config.ambientColor,
      intensity: config.ambientIntensity,
    ),
    for (final light in config.lights)
      LightComponent.point(
        position: Vector3(light.x, light.y, light.z),
        color: light.color,
        intensity: light.intensity,
      ),
  ];

  /// Ortamı, ışıkları, gökyüzünü ve zemini mevcut bölüme göre değiştirir.
  void _applyLevel() {
    final previous = _appliedLevel;
    if (previous == levelIndex) return;
    if (previous != null) {
      world.remove(_environments[previous]);
      world.removeAll(_levelLights[previous]);
    }
    world
      ..add(_environments[levelIndex])
      ..addAll(_levelLights[levelIndex]);
    _groundMaterial.albedoColor = _matte(level.ground).albedoColor;
    _sky.configure(
      top: level.skyTop,
      horizon: level.skyHorizon,
      sunAndClouds: level.sunAndClouds,
    );
    _snowfall.active = level.snow;
    _leader = _leaders[level.leaderModel]!;
    for (final leader in _leaders.values) {
      leader.visible = leader == _leader;
    }
    _appliedLevel = levelIndex;
  }

  /// Işık almayan mat malzeme. flame_3d shader'ı sonuca gamma düzeltmesi
  /// uyguladığı için rengi önce doğrusal (linear) uzaya çeviriyoruz; yoksa
  /// renkler soluk çıkıyor.
  static SpatialMaterial _matte(Color color) {
    double linear(double c) => pow(c, 2.2).toDouble();
    return SpatialMaterial(
      albedoColor: Color.from(
        alpha: 1,
        red: linear(color.r),
        green: linear(color.g),
        blue: linear(color.b),
      ),
      metallic: 0,
      roughness: 1,
    );
  }

  // --- Müzik ---------------------------------------------------------------

  /// Müzik açıksa ve henüz çalmıyorsa başlatır. Web'de tarayıcı ilk dokunuştan
  /// önce sese izin vermez; bu yüzden butonlarda da tekrar denenir.
  Future<void> _ensureMusic() async {
    if (!profile.musicOn.value || _musicStarted || _musicLoading) return;
    _musicLoading = true;
    try {
      await FlameAudio.bgm.play(_musicFile, volume: 0.45);
      _musicStarted = FlameAudio.bgm.isPlaying;
      // Yüklenirken müzik kapatıldıysa hemen sustur.
      if (!profile.musicOn.value) await FlameAudio.bgm.pause();
    } catch (_) {
      // Tarayıcı engelledi; bir sonraki dokunuşta yeniden denenir.
    } finally {
      _musicLoading = false;
    }
  }

  /// Menüdeki ses butonu: müziği açar / kapatır ve tercihi kaydeder.
  Future<void> toggleMusic() async {
    final on = !profile.musicOn.value;
    final saved = profile.setMusicOn(on);
    if (on) {
      if (_musicStarted) {
        await FlameAudio.bgm.resume();
      } else {
        await _ensureMusic();
      }
    } else {
      await FlameAudio.bgm.pause();
    }
    await saved;
  }

  @override
  void onRemove() {
    FlameAudio.bgm.dispose();
    super.onRemove();
  }

  // --- Oyun akışı -----------------------------------------------------------

  /// "Tekrar Oyna" ve diğer başlatmalar: mevcut bölümü baştan oynatır.
  void startGame() {
    if (!isLoaded) return; // modeller henüz yükleniyor
    _ensureMusic();
    resumeEngine();
    overlays.removeAll([
      overlayMenu,
      overlayGameOver,
      overlayLevelComplete,
      overlayFinished,
    ]);
    overlays.add(overlayOptions);
    profile.setLastLevel(levelIndex);
    _applyLevel();
    _resetRound();
    _planEliminations();
    phase = GamePhase.intro;
    camera.startIntro();
    _hud.showPortraits = true;
  }

  /// Bölümün yanma anlarını seçer: sürenin %15–%85'i arasına rastgele. Son
  /// bölümde kalan herkes yanar, sonuncusu en geç sürenin %75'inde; böylece
  /// oyuncu süre bitmeden tek başına kalıp kazanır.
  void _planEliminations() {
    final alive = _npcs.length - _outSlots.length;
    final (low, high) = level.eliminations;
    final count = level.lastOneStanding
        ? alive
        : min(low + _random.nextInt(high - low + 1), alive - 1);
    final (from, to) = level.lastOneStanding ? (0.2, 0.75) : (0.15, 0.85);
    _eliminationTimes
      ..clear()
      ..addAll([
        for (var i = 0; i < count; i++)
          levelDuration * (from + _random.nextDouble() * (to - from)),
      ])
      ..sort();
  }

  /// Menüden bir bölüm seçildi (oynanamıyorsa bir şey olmaz). Sıra, o bölüme
  /// kadar yanmış olması gereken sayıda kişi eksik başlar (bkz.
  /// [eliminatedBefore]); son bölüme menüden girilse de yanında 1–2 kişi kalır.
  void startLevel(int index) {
    if (!profile.isPlayable(index)) return;
    levelIndex = index;
    _outSlots.clear();
    final (low, high) = eliminatedBefore(index, npcCount: _npcs.length);
    final out = low + _random.nextInt(high - low + 1);
    final slots = [for (final npc in _npcs) _slotOf[npc]!]..shuffle(_random);
    _outSlots.addAll(slots.take(out));
    startGame();
  }

  /// Ana menüdeki "Yeni Oyun": ilerleme sıfırlanır, 1. bölümden başlanır.
  Future<void> newGame() async {
    final saved = profile.resetProgress();
    startLevel(0);
    await saved;
  }

  /// "Sonraki Bölüm" butonu.
  void nextLevel() {
    if (isLastLevel) return;
    levelIndex++;
    startGame();
  }

  /// "Baştan Başla" butonu (son bölüm bitince).
  void restartFromFirstLevel() {
    if (!profile.isPlayable(0)) return;
    levelIndex = 0;
    _outSlots.clear();
    startGame();
  }

  /// "Ana Menü" butonu. Arkada en son oynanan bölümün sahnesi kalır.
  void backToMenu() {
    resumeEngine();
    overlays.removeAll([
      overlayGameOver,
      overlayLevelComplete,
      overlayFinished,
      overlayOptions,
    ]);
    _outSlots.clear();
    _pickMenuLevel();
    _applyLevel();
    _resetRound();
    phase = GamePhase.menu;
    camera.showMenuView();
    overlays.add(overlayMenu);
  }

  void _resetRound() {
    _freezing = false;
    _endEnemyBlind();
    _nextEnemyBlind = _randomIn(_enemyBlindGap);
    _nextRivalTaunt = _firstRivalTaunt + _randomIn(_rivalTauntGap) / 2;
    _endBlind();
    _endShield();
    _lives = profile.maxLives;
    _hud.setLives(_lives, profile.maxLives);
    _reversed = false;
    _hud.reversed = false;
    _nextReverseToggle = _randomIn(_normalPhase);
    _required = Pose.stand;
    _playerPose = Pose.stand;
    _comboNext = null;
    _later.clear();
    _deadline = null;
    _gameOverDelay = 0;
    _levelCompleteDelay = 0;
    _levelTime = 0;
    _pendingEliminations.clear();
    for (final gate in _gates) {
      gate.reset();
    }
    _hud
      ..clear()
      ..clearEliminations()
      ..showPortraits = false
      ..levelLabel = null
      ..timeLeft = null;
    _leader.resetPose();
    for (final npc in _npcs) {
      npc.resetPose();
      final slot = _slotOf[npc]!;
      if (_outSlots.contains(slot)) {
        npc.removeFromRow();
        _hud.markEliminated(_portraitIndex(slot), animate: false);
      }
    }
    _player.resetPose();
  }

  @override
  void update(double dt) {
    super.update(dt);
    // Birinci şahısta kamera oyuncunun kafasının içinde: kendi modelini gizle.
    _player.visible = !camera.insideHead;
    _updateGates(dt);
    _updateEliminations(dt);
    switch (phase) {
      case GamePhase.menu:
        break;
      case GamePhase.intro:
        if (camera.introFinished) {
          phase = GamePhase.playing;
          _hud
            ..showText(L.levelTitle(level.number), fontSize: 30)
            ..levelLabel = L.levelWithName(level.number)
            ..timeLeft = levelDuration;
          _untilCommand = 2.0;
          // Yeni kural varsa bölüm adından sonra anlatılır; ilk komut bekler.
          final tip = level.tip;
          if (tip != null) {
            _hud.showTip(tip, delay: 1.2);
            _untilCommand = 5.0;
          }
        }
      case GamePhase.playing:
        _updateRules(dt);
      case GamePhase.gameOver:
        if (_gameOverDelay > 0) {
          _gameOverDelay -= dt;
          // Yanma animasyonu görünsün diye ekran biraz gecikmeli açılır.
          if (_gameOverDelay <= 0) overlays.add(overlayGameOver);
        }
      case GamePhase.levelComplete:
        if (_levelCompleteDelay > 0) {
          _levelCompleteDelay -= dt;
          if (_levelCompleteDelay <= 0) {
            overlays.add(isLastLevel ? overlayFinished : overlayLevelComplete);
          }
        }
    }
  }

  void _updateRules(double dt) {
    // Kamera yanan bir oyuncuyu izlerken komut gelmez, süre işlemez.
    if (camera.isGlancing) return;

    _levelTime += dt;
    _hud.timeLeft = max(0, levelDuration - _levelTime);
    _runLater(dt);
    _updateBlind(dt);
    _updateShield(dt);
    _updateEnemyBlind(dt);
    _updateRivalTaunts();
    if (_levelTime >= levelDuration || _wonAsLastOne) {
      _completeLevel();
      return;
    }

    final deadline = _deadline;
    if (deadline != null) {
      _deadline = deadline - dt;
      if (_deadline! <= 0) {
        _deadline = null;
        if (_playerPose != _required) {
          _mistake(L.tooLate);
          return;
        }
      }
    }

    _untilCommand -= dt;
    if (_untilCommand <= 0) _issueCommand();
  }

  /// Sırada kalanlardan rastgele biri ters kontrolü "atar": portresi
  /// titrer, yanında laf sokan balon çıkar, altta kimin yaptığı yazar.
  void _castReverseByNpc() {
    final alive = _npcs.where((npc) => !npc.eliminated).toList();
    if (alive.isEmpty) return;
    final caster = alive[_random.nextInt(alive.length)];
    final index = _portraitIndex(_slotOf[caster]!);
    _hud
      ..taunt(index, L.taunt(1 + _random.nextInt(L.tauntCount)))
      ..toast(L.flippedBy(characterNames[index]), color: Hud.reverseColor);
  }

  void _runLater(double dt) {
    for (var i = _later.length - 1; i >= 0; i--) {
      final (left, job) = _later[i];
      if (left - dt > 0) {
        _later[i] = (left - dt, job);
      } else {
        _later.removeAt(i);
        job();
      }
    }
  }

  /// Çift komut: lider iki komutu art arda söyler ve gösterir. Oyuncu önce
  /// birinciyi yapar; yapınca ikincisi için yeniden tepki süresi başlar.
  /// Birinci komut her zaman bir hareket ister (oyuncunun şu anki pozunun tersi).
  static const double _comboGap = 0.6;

  void _issueDoubleCommand() {
    final first = _required.opposite;
    final second = first.opposite;
    _leader.gesture(first);
    _later.add((_comboGap, () => _leader.gesture(second)));
    for (final npc in _npcs) {
      if (npc.eliminated) continue;
      final delay = 0.15 + _random.nextDouble() * 0.35;
      npc.setCrouched(first == Pose.crouch, delay: delay);
      _later.add((
        delay + _comboGap,
        () => npc.setCrouched(second == Pose.crouch, delay: 0.1),
      ));
    }
    _required = first;
    _comboNext = second;
    _hud
      ..showDoubleCommand(first, second)
      ..toast(L.doubleCommand, color: Hud.freezeColor);
    _deadline = level.reactionTime;
    // İki adım da bitsin diye sonraki komut bekler.
    _untilCommand = level.reactionTime * 2 + level.commandInterval * 0.6;
  }

  double _randomIn((double, double) range) =>
      range.$1 + _random.nextDouble() * (range.$2 - range.$1);

  void _issueCommand() {
    _freezing = false;
    // Kontrol tersliği: zamanı gelince bu komutun yerine duyuru yapılır ve
    // okunsun diye bir sonraki komut biraz gecikir.
    if (level.reverseControls &&
        _deadline == null &&
        _levelTime >= _nextReverseToggle) {
      // Kalkan varken kontrolleri kimse bozamaz.
      if (!_reversed && _shielded) {
        _nextReverseToggle = _levelTime + _randomIn(_normalPhase);
        _hud.toast(L.shieldBlocked, color: Hud.shieldColor);
        _untilCommand = 0.6;
        return;
      }
      _reversed = !_reversed;
      // Kontrolleri sıradakilerden biri bozar: portresi titreyip laf sokar.
      if (_reversed) _castReverseByNpc();
      _hud
        ..reversed = _reversed
        ..showText(
          _reversed ? L.controlsReversed : L.controlsNormal,
          color: _reversed ? Hud.reverseColor : Hud.deveColor,
        )
        ..flash(_reversed ? Hud.reverseColor : Hud.deveColor, alpha: 0.2);
      _nextReverseToggle =
          _levelTime + (_reversed ? _reversePhase : _randomIn(_normalPhase));
      _untilCommand = 1.6;
      return;
    }
    // Şaşırtma: oyuncu doğru pozdayken (bekleyen komut yokken) arada bir
    // komut yerine "SABİT KAL!" gelir; kimse kıpırdamaz.
    if (_deadline == null && _random.nextDouble() < level.freezeChance) {
      _freezing = true;
      _hud
        ..showFreeze()
        ..flash(Hud.freezeColor, alpha: 0.15);
      _untilCommand =
          level.commandInterval * (1.0 + _random.nextDouble() * 0.4);
      return;
    }

    if (_deadline == null && _random.nextDouble() < level.doubleChance) {
      _issueDoubleCommand();
      return;
    }

    final word = _random.nextDouble() < level.repeatChance
        ? _required
        : _required.opposite;

    // Kandırma: oyun kurucu söylediğinin tersini yapar. Oyuncu kelimeye uymalı.
    final tricked = _random.nextDouble() < level.trickChance;
    _leader.gesture(tricked ? word.opposite : word);

    // Sırası gelen yanma: sıradakilerden rastgele biri bu komutta hata yapar.
    Character? victim;
    if (_eliminationTimes.isNotEmpty && _levelTime >= _eliminationTimes.first) {
      _eliminationTimes.removeAt(0);
      final alive = _npcs.where((npc) => !npc.eliminated).toList();
      // Son bölüm dışında sırada en az bir kişi kalır.
      if (alive.length > 1 || (level.lastOneStanding && alive.isNotEmpty)) {
        victim = alive[_random.nextInt(alive.length)];
      }
    }

    for (final npc in _npcs) {
      if (npc.eliminated) continue;
      final delay = 0.15 + _random.nextDouble() * 0.35;
      if (npc == victim) {
        // Hata: son pozu yanlış kalır (ya ters yöne gider ya da hiç kıpırdamaz).
        // Yanınca kendi tarafına doğru çapraz yürüyüp oyun kurucunun hizasında,
        // ondan uzakta kaybolur (ileride oraya bir kapı gelecek).
        npc
          ..setCrouched(word != Pose.crouch, delay: delay)
          ..eliminateAfter(level.reactionTime + 0.1, walkTo: _exitPoint(npc));
        _pendingEliminations.add((level.reactionTime + 0.1, npc));
      } else {
        npc.setCrouched(word == Pose.crouch, delay: delay);
      }
    }

    _required = word;
    _hud.showCommand(word);
    if (tricked) _hud.showTrick();
    _deadline = _playerPose == _required ? null : level.reactionTime;
    _untilCommand = level.commandInterval * (0.8 + _random.nextDouble() * 0.4);
  }

  void _movePlayer(Pose pose) {
    if (paused || phase != GamePhase.playing || pose == _playerPose) return;
    _setPlayerPose(pose);
    if (_freezing) {
      _mistake(L.shouldStayStill);
    } else if (pose != _required) {
      _mistake(L.wrongMove);
    } else {
      final next = _comboNext;
      if (next != null) {
        // Çift komutun birinci yarısı tamam; şimdi ikincisi.
        _comboNext = null;
        _required = next;
        _deadline = level.reactionTime;
        _hud.showCommand(next);
      } else {
        _deadline = null;
      }
      _hud.flash(Hud.deveColor, alpha: 0.18);
    }
  }

  /// Hata: can varsa bir can gider ve oyun sürer, yoksa yanılır.
  void _updateBlind(double dt) {
    if (_blindLeft <= 0) return;
    _blindLeft -= dt;
    _hud.blindLeft = max(0, _blindLeft);
    if (_blindLeft > 0) return;
    _endBlind();
    // Kör iken yanlış pozda kaldıysan, lider görmeye başlayınca düzeltmek
    // için normal tepki süren olur.
    if (!_freezing && _playerPose != _required) _deadline = level.reactionTime;
  }

  void _mistake(String reason) {
    _comboNext = null;
    // Lider kör: hata görülmez, can gitmez.
    if (_blindLeft > 0) {
      _deadline = null;
      _hud.toast(L.leaderMissed);
      return;
    }
    _lives--;
    _hud.setLives(_lives, profile.maxLives);
    if (_lives <= 0) {
      _lose(reason);
      return;
    }
    // Oyuncu doğru poza geri alınır; kısa bir nefes payıyla devam edilir.
    _freezing = false;
    _deadline = null;
    _setPlayerPose(_required);
    _playBuzzer();
    _hud
      ..showText(L.minusLife, color: Hud.loseColor)
      ..toast(reason)
      ..flash(Hud.loseColor, alpha: 0.3);
    camera.shake(strength: 0.15, duration: 0.35);
    _untilCommand = max(_untilCommand, 1.6);
  }

  void _setPlayerPose(Pose pose) {
    _playerPose = pose;
    _player.setCrouched(pose == Pose.crouch);
    camera.crouched = pose == Pose.crouch;
  }

  void _lose(String reason) {
    phase = GamePhase.gameOver;
    loseReason = reason;
    _deadline = null;
    _endBlind();
    _endShield();
    _endEnemyBlind();
    _hud
      ..reversed =
          false // sonuç kartının üstünde uyarı şeridi kalmasın
      ..showText(L.outBig, color: Hud.loseColor);
    _playBuzzer();
    _hud.flash(Hud.loseColor);
    camera
      ..showLoseView()
      ..shake();
    _player.fail();
    _gameOverDelay = 1.2;
  }

  /// Süre doldu: bölüm tamam. Kalanlar sevinir, kamera geri çekilir.
  void _completeLevel() {
    phase = GamePhase.levelComplete;
    _deadline = null;
    _pendingEliminations.clear();
    _endBlind();
    _endShield();
    _endEnemyBlind();
    _hud.reversed = false;
    // Bu bölümde yananlar sonraki bölümlerde sırada olmaz.
    for (final npc in _npcs) {
      if (npc.eliminated) _outSlots.add(_slotOf[npc]!);
    }
    _hud
      ..showText(isLastLevel ? L.wonBig : L.levelDoneBig, color: Hud.deveColor)
      ..flash(Hud.deveColor, alpha: 0.3)
      ..timeLeft = 0;
    for (final npc in _npcs) {
      if (!npc.eliminated) npc.cheer();
    }
    _player.cheer();
    _leader.cheer();
    camera.showLoseView();
    _levelCompleteDelay = 1.6;
    profile.completeLevel(levelIndex);
    lastReward = _rewardFor(level, livesLeft: _lives);
    profile.addCoins(lastReward);
  }

  /// Son bitirilen bölümde kazanılan altın (sonuç kartında gösterilir).
  int lastReward = 0;

  /// Bölüm ödülü: zor bölümler daha çok verir, kalan her can bonus.
  static int _rewardFor(LevelConfig level, {required int livesLeft}) =>
      10 + 5 * level.number + 5 * livesLeft;

  /// Yanan oyuncular kendi tarafındaki kapıya yürüyüp içinde kaybolur.
  /// Kapılar oyun kurucunun hizasında, iki yanda; kemerleri yananların geldiği
  /// yöne, yani sırada kendi tarafının ortasına bakar. Bütün bölüm
  /// sahnelerinde bu alan boştur (tools/build_*.py).
  static const double gateX = 6.5;

  /// Kapının kemerini sırada kendi tarafının ortasına çevirir. Model kendi
  /// -Z'sine bakıyor (tools/build_gate.py); Y ekseninde θ dönünce -Z,
  /// (-sin θ, -cos θ) yönüne gelir.
  static Quaternion _gateFacing(double gateX) {
    // Solda 0–2. yerler, sağda (oyuncudan sonra) 4–5. yerler.
    final sideCenter = gateX < 0
        ? _slotX(1)
        : (_slotX(playerSlot + 1) + _slotX(rowSize - 1)) / 2;
    final toRowX = sideCenter - gateX;
    const toRowZ = 0 - leaderZ;
    return Quaternion.axisAngle(Vector3(0, 1, 0), atan2(-toRowX, -toRowZ));
  }

  Vector3 _exitPoint(Character npc) =>
      Vector3(npc.position.x < 0 ? -gateX : gateX, 0, leaderZ);

  final List<Gate> _gates = [];

  /// Son bölümde sıradaki herkes yandı ve kapıdan çıktı: oyuncu tek başına
  /// kaldı, bölüm (ve oyun) kazanıldı.
  bool get _wonAsLastOne =>
      level.lastOneStanding &&
      _pendingEliminations.isEmpty &&
      _npcs.every((npc) => npc.gone);

  /// Yanan biri kapıya bu kadar yaklaşınca kanatlar açılır; içeride
  /// kaybolunca kapanır.
  static const double _gateOpenDistance = 3;

  void _updateGates(double dt) {
    for (final gate in _gates) {
      gate
        ..wantOpen = _npcs.any(
          (npc) =>
              npc.eliminated &&
              npc.visible &&
              npc.position.distanceTo(gate.position) < _gateOpenDistance,
        )
        ..update(dt);
    }
  }

  /// Hata yapan NPC yandığı anda haber verir ve sayacı düşürür.
  void _updateEliminations(double dt) {
    for (var i = _pendingEliminations.length - 1; i >= 0; i--) {
      final (left, npc) = _pendingEliminations[i];
      if (left - dt > 0) {
        _pendingEliminations[i] = (left - dt, npc);
        continue;
      }
      _pendingEliminations.removeAt(i);
      final slot = _slotOf[npc]!;
      _playBuzzer();
      _hud
        ..toast(_eliminationMessage(slot))
        ..markEliminated(_portraitIndex(slot));
      // Başımızı yanan oyuncuya çevirip gözden kaybolana kadar izleriz; bu
      // sırada oyun duraklar (bkz. _updateRules).
      camera.glanceAt(
        () => npc.position + Vector3(0, 1.1, 0),
        until: () => npc.gone,
      );
    }
  }

  /// Birinci şahısta yanlar görünmediği için kimin yandığını yazıyla söyler:
  /// "◀ Emma yandı!" (ok, yananın hangi tarafta olduğunu gösterir).
  /// Kamera -Z'ye baktığından küçük sıra numarası solda kalır.
  static String _eliminationMessage(int slot) {
    final message = L.isOut(characterNames[_portraitIndex(slot)]);
    return slot < playerSlot ? '◀ $message' : '$message ▶';
  }

  // --- Girdi ----------------------------------------------------------------

  @override
  void onDragStart(DragStartEvent event) {
    super.onDragStart(event);
    _dragDy = 0;
  }

  @override
  void onDragUpdate(DragUpdateEvent event) {
    super.onDragUpdate(event);
    _dragDy += event.deviceDelta.y;
  }

  @override
  void onDragEnd(DragEndEvent event) {
    super.onDragEnd(event);
    if (_dragDy.abs() < 30) return;
    _swipe(up: _dragDy < 0);
  }

  /// Kaydırma yönünü poza çevirir; kontroller tersse yukarı CÜCE olur.
  void _swipe({required bool up}) =>
      _movePlayer(up != _reversed ? Pose.stand : Pose.crouch);

  /// Test için yukarı / aşağı ok tuşları.
  @override
  KeyEventResult onKeyEvent(
    KeyEvent event,
    Set<LogicalKeyboardKey> keysPressed,
  ) {
    if (event is KeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.arrowUp) {
        _swipe(up: true);
        return KeyEventResult.handled;
      }
      if (event.logicalKey == LogicalKeyboardKey.arrowDown) {
        _swipe(up: false);
        return KeyEventResult.handled;
      }
    }
    return super.onKeyEvent(event, keysPressed);
  }
}
