import 'dart:math';
import 'dart:ui' as ui;

import 'package:flame/components.dart';
import 'package:flutter/material.dart';

import '../l10n/strings.dart';
import 'pose.dart';

class Hud extends Component with HasGameReference {
  static const Color deveColor = Color(0xFF7CFC5A);
  static const Color cuceColor = Color(0xFFFFB13B);
  static const Color loseColor = Color(0xFFFF4D4D);
  static const Color freezeColor = Color(0xFF4FD8FF);
  static const Color reverseColor = Color(0xFFFF4FD8);

  /// Menüdeki yeşil: portre çerçeveleri ve ipucu kutusunun kenarı.
  static const Color frameColor = Color(0xFF8BE04E);

  /// Kalkan: uyarılar ve şerit bu renkte.
  static const Color shieldColor = Color(0xFFFFC83A);

  /// "Kör Et" sürerken kalan süre (sn); 0 iken gösterilmez.
  double blindLeft = 0;
  final _blindText = TextPaint(
    style: const TextStyle(
      fontSize: 20,
      fontWeight: FontWeight.w900,
      color: Color(0xFF0E2A33),
      letterSpacing: 0.5,
    ),
  );
  final Paint _blindPaint = Paint()..color = const Color(0xE6B4EEFF);

  /// Kalkan sürerken kalan süre (sn); 0 iken gösterilmez.
  double shieldLeft = 0;
  final Paint _shieldPaint = Paint()..color = const Color(0xE6FFD66B);

  /// Kontroller ters iken altta nabız gibi atan uyarı şeridi.
  bool reversed = false;
  final _reverseText = TextPaint(
    style: const TextStyle(
      fontSize: 22,
      fontWeight: FontWeight.w900,
      color: Colors.white,
      letterSpacing: 1,
    ),
  );
  final Paint _reversePaint = Paint();
  double _clock = 0;
  static const double _popDuration = 0.25;
  static const double _flashDuration = 0.5;

  double _popTime = _popDuration;

  /// Büyük yazı; metin değişince bir kez dizilir (her karede değil).
  TextPainter? _textPainter;

  Color _flashColor = Colors.transparent;
  double _flashMaxAlpha = 0;
  double _flashTime = _flashDuration;

  final Paint _flashPaint = Paint();

  /// Portreler yalnızca oyun sırasında çizilir.
  bool showPortraits = false;

  /// Sol üstte bölüm adı ve kalan süre (saniye); null iken gösterilmez.
  String? levelLabel;
  double? timeLeft;

  static const double _toastDuration = 2.2;
  String _toast = '';
  double _toastTime = _toastDuration;

  /// Soldaki portre sütunu: diğer oyuncuların resmi (oyuncunun kendisi yok),
  /// sıradaki yerlerine göre soldan sağa → yukarıdan aşağı. Yanan oyuncunun
  /// portresi önce titrer, sonra üstüne kırmızı çarpı çizilir.
  List<ui.Image> portraits = [];

  /// Portrelerin altında yazan isimler (portrelerle aynı sırada).
  List<String> portraitNames = [];
  final _nameText = TextPaint(
    style: const TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w800,
      color: Colors.white,
      shadows: [Shadow(blurRadius: 4, color: Colors.black)],
    ),
  );

  /// Laf sokan karakter: portresi titrer, yanında konuşma balonu çıkar.
  int? _tauntIndex;
  double _tauntTime = 99;
  TextPainter? _tauntPainter;
  static const double _tauntDuration = 2.8;
  static const double _tauntShake = 0.6;
  final Paint _bubblePaint = Paint()..color = const Color(0xF2FFFFFF);
  final Paint _bubbleBorder = Paint()
    ..style = PaintingStyle.stroke
    ..strokeWidth = 2.5
    ..color = reverseColor;

  /// Bir konuşma balonu hâlâ ekranda mı.
  bool get tauntShowing => _tauntTime < _tauntDuration;

  /// [index]'teki karakter laf sokar ([text]).
  void taunt(int index, String text) {
    _tauntIndex = index;
    _tauntTime = 0;
    _tauntPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w800,
          color: Color(0xFF1A1A22),
        ),
      ),
      // Arapça gibi sağdan sola dillerde kelime sırası doğru dizilsin.
      textDirection: L.language.rtl ? TextDirection.rtl : TextDirection.ltr,
    )..layout(maxWidth: 150);
  }

  /// Yananların portre indeksi → yandığından beri geçen süre.
  final Map<int, double> _eliminated = {};
  static const double _shakeDuration = 0.7;

  static const double _portraitSize = 50;

  /// Portreler arası; altındaki isme yer kalsın.
  static const double _portraitGap = 24;

  /// Sol üstteki bölüm/süre yazısının, büyük yazının (y 125) ve "yandı"
  /// haberinin (y 185) altından başlar.
  static const double _portraitTop = 215;
  final Paint _portraitPaint = Paint()..filterQuality = FilterQuality.none;
  final Paint _portraitFade = Paint()..color = const Color(0x99000000);
  final Paint _crossPaint = Paint()
    ..color = loseColor
    ..strokeWidth = 6
    ..strokeCap = StrokeCap.round;
  final Paint _framePaint = Paint()
    ..style = PaintingStyle.stroke
    ..strokeWidth = 3;

  final _labelText = TextPaint(
    style: const TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.bold,
      color: Colors.white,
      shadows: [Shadow(blurRadius: 6, color: Colors.black87)],
    ),
  );

  /// Komutun altında birkaç saniye görünen kısa haber ("Solundaki oyuncu yandı!").
  Color _toastColor = loseColor;

  void toast(String text, {Color color = loseColor}) {
    _toast = text;
    _toastColor = color;
    _toastTime = 0;
  }

  /// Komut oku (assets/images/icons/arrow.png; resim sağa bakıyor). Yüklenene
  /// kadar null; o zaman yalnızca yazı gösterilir.
  ui.Image? arrow;

  /// Resmin boş kenarları hariç okun kendisi (256 piksele küçültülmüş hâlde).
  static const Rect _arrowSource = Rect.fromLTRB(45, 59, 211, 196);
  static const double _arrowSize = 64;
  static const double _arrowGap = 10;

  /// Yazının solunda çizilecek okun açısı; null iken ok yok.
  double? _arrowAngle;
  final Paint _arrowPaint = Paint()..filterQuality = FilterQuality.medium;

  void showCommand(Pose pose) {
    final color = pose == Pose.stand ? deveColor : cuceColor;
    showText('${pose.word}!', color: color);
    _arrowAngle = pose == Pose.stand ? -pi / 2 : pi / 2;
    _arrowPaint.colorFilter = _tint(color);
  }

  /// Çift komut: iki satırda, her kelime kendi renginde ("DEVE," / "CÜCE!").
  /// Altındaki "ÇİFT KOMUT!" uyarısına binmesin diye tek komuttan küçük.
  void showDoubleCommand(Pose first, Pose second) {
    showText('');
    Color colorOf(Pose pose) => pose == Pose.stand ? deveColor : cuceColor;
    _textPainter = TextPainter(
      text: TextSpan(
        style: const TextStyle(
          fontSize: 34,
          height: 1.05,
          fontWeight: FontWeight.w900,
          shadows: [Shadow(blurRadius: 10, color: Colors.black87)],
        ),
        children: [
          TextSpan(
            text: '${first.word},\n',
            style: TextStyle(color: colorOf(first)),
          ),
          TextSpan(
            text: '${second.word}!',
            style: TextStyle(color: colorOf(second)),
          ),
        ],
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    )..layout();
  }

  /// Oku komutun rengine boyar: önce gri tonlara çevirir (gölgeler korunur),
  /// sonra renkle çarpar. 1.7 çarpanı okun açık tonlarını parlak tutar.
  static ColorFilter _tint(Color color) {
    const k = 1.7;
    List<double> row(double c) => [
      0.3 * c * k,
      0.59 * c * k,
      0.11 * c * k,
      0,
      0,
    ];
    return ColorFilter.matrix([
      ...row(color.r),
      ...row(color.g),
      ...row(color.b),
      0,
      0,
      0,
      1,
      0,
    ]);
  }

  /// Sol alttaki canlar (assets/images/icons/heart.png). Giden can gri ve soluk
  /// çizilir; gittiği an titreyip küçülür.
  ui.Image? heart;
  int _lives = 0;
  int _maxLives = 0;
  double _lifeLostTime = 99;
  static const double _heartSize = 28;
  static const double _heartGap = 6;

  /// Resmin boş kenarları hariç kalbin kendisi (128 piksele küçültülmüş hâlde).
  static const Rect _heartSource = Rect.fromLTRB(11, 54, 117, 140);
  final Paint _heartPaint = Paint()..filterQuality = FilterQuality.none;
  final Paint _lostHeartPaint = Paint()
    ..filterQuality = FilterQuality.none
    ..colorFilter = const ColorFilter.matrix([
      0.3, 0.59, 0.11, 0, 0, //
      0.3, 0.59, 0.11, 0, 0,
      0.3, 0.59, 0.11, 0, 0,
      0, 0, 0, 0.35, 0,
    ]);

  void setLives(int lives, int maxLives) {
    if (lives < _lives) _lifeLostTime = 0;
    _lives = lives;
    _maxLives = maxLives;
  }

  /// Lider kandırınca (söylediğinin tersini yapınca) komutun üstünde kısa
  /// süre yanıp sönen küçük "KANDIRMA!" yazısı.
  double _trickTime = 99;
  static const double _trickDuration = 1.4;
  final _trickText = TextPaint(
    style: const TextStyle(
      fontSize: 18,
      fontWeight: FontWeight.w900,
      color: Color(0xFFFFE14D),
      letterSpacing: 1,
      shadows: [Shadow(blurRadius: 4, color: Colors.black)],
    ),
  );

  void showTrick() => _trickTime = 0;

  /// Bölüm başında yeni kuralı anlatan ipucu kutusu (ekranın ortasında).
  String? _tip;
  double _tipTime = 0;
  TextPainter? _tipPainter;
  double _tipLaidOutWidth = 0;
  static const double _tipDuration = 3.4;
  final Paint _tipPaint = Paint()..color = const Color(0xD9101820);
  final Paint _tipBorder = Paint()
    ..style = PaintingStyle.stroke
    ..strokeWidth = 3
    ..color = frameColor;

  /// [delay] saniye sonra [text]'i birkaç saniye gösterir.
  void showTip(String text, {double delay = 0}) {
    _tip = text;
    _tipTime = -delay;
    _tipPainter = null;
  }

  /// "SABİT KAL!" şaşırtması: komutun yerinde (portrelerin üstünde) nabız
  /// gibi atan yazı. Bir sonraki komut ya da yazıyla kalkar.
  TextPainter? _freezePainter;
  double _freezeTime = 0;

  void showFreeze() {
    _textPainter = null;
    _freezeTime = 0;
    _freezePainter = TextPainter(
      text: TextSpan(
        text: L.stayStill,
        style: const TextStyle(
          fontSize: 40,
          fontWeight: FontWeight.w900,
          color: freezeColor,
          shadows: [Shadow(blurRadius: 12, color: Colors.black)],
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
  }

  /// Ortada büyüyüp yerine oturan büyük yazı; satırlara "\n" ile bölünebilir.
  /// Komutlar 40; uzun bölüm adları gibi yazılar daha küçük [fontSize] ile.
  void showText(
    String text, {
    Color color = Colors.white,
    double fontSize = 40,
  }) {
    _popTime = 0;
    _trickTime = _trickDuration; // yeni yazıyla eski uyarı kalkar
    _freezePainter = null;
    _arrowAngle = null;
    _textPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          fontSize: fontSize,
          height: 1.05,
          fontWeight: FontWeight.w900,
          color: color,
          shadows: const [Shadow(blurRadius: 10, color: Colors.black87)],
        ),
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    )..layout();
  }

  void clear() {
    _tip = null;
    _tauntIndex = null;
    _textPainter = null;
    _freezePainter = null;
    _toastTime = _toastDuration;
  }

  /// [index]'teki portre titrer ve çarpılanır. [animate] false ise (önceki
  /// bölümde yanmış) doğrudan çarpılı gösterilir.
  void markEliminated(int index, {bool animate = true}) {
    _eliminated[index] = animate ? 0 : _shakeDuration;
  }

  void clearEliminations() => _eliminated.clear();

  void flash(Color color, {double alpha = 0.45}) {
    _flashColor = color;
    _flashMaxAlpha = alpha;
    _flashTime = 0;
  }

  @override
  void update(double dt) {
    super.update(dt);
    _popTime += dt;
    _flashTime += dt;
    _toastTime += dt;
    _freezeTime += dt;
    _clock += dt;
    _trickTime += dt;
    _tauntTime += dt;
    _tipTime += dt;
    _lifeLostTime += dt;
    _eliminated.updateAll((_, since) => since + dt);
  }

  @override
  void render(Canvas canvas) {
    final size = game.size;

    if (_flashTime < _flashDuration) {
      final alpha = _flashMaxAlpha * (1 - _flashTime / _flashDuration);
      _flashPaint.color = _flashColor.withValues(alpha: alpha);
      canvas.drawRect(Rect.fromLTWH(0, 0, size.x, size.y), _flashPaint);
    }

    final painter = _textPainter;
    if (painter != null) {
      final t = min(1.0, _popTime / _popDuration);
      const c = 1.7;
      final ease = 1 + (c + 1) * pow(t - 1, 3) + c * pow(t - 1, 2);
      final image = arrow;
      final angle = _arrowAngle;
      final withArrow = image != null && angle != null;
      // Ok varsa yazının solunda; ikisi birlikte ortalanır.
      final width = painter.width + (withArrow ? _arrowSize + _arrowGap : 0);
      // Büyüyüp oturma efekti; ama hiçbir anda ekranın enini aşmasın.
      final fit = (size.x - 32) / width;
      final scale = min(1.6 - 0.6 * ease, fit);
      canvas
        ..save()
        ..translate(size.x / 2, 125)
        ..scale(scale);
      if (withArrow) {
        final aspect = _arrowSource.height / _arrowSource.width;
        canvas
          ..save()
          ..translate(-width / 2 + _arrowSize / 2, 0)
          ..rotate(angle)
          ..drawImageRect(
            image,
            _arrowSource,
            Rect.fromCenter(
              center: Offset.zero,
              width: _arrowSize,
              height: _arrowSize * aspect,
            ),
            _arrowPaint,
          )
          ..restore();
      }
      painter.paint(
        canvas,
        Offset(width / 2 - painter.width, -painter.height / 2),
      );
      canvas.restore();
    }

    if (reversed) _renderReverseBanner(canvas, size);
    if (blindLeft > 0) {
      _renderTimerBanner(
        canvas,
        Offset(size.x / 2, size.y - 162),
        L.leaderBlind(blindLeft.ceil()),
        blindLeft / 4,
        _blindPaint,
      );
    }
    if (shieldLeft > 0) {
      // Lider kör şeridiyle aynı anda olabilir: onun üstünde.
      _renderTimerBanner(
        canvas,
        Offset(size.x / 2, size.y - 210),
        L.shieldActive(shieldLeft.ceil()),
        shieldLeft / 15,
        _shieldPaint,
      );
    }
    _renderTip(canvas, size);

    // Yanıp sönme: saniyede ~4 kez görünür / kaybolur.
    if (_trickTime < _trickDuration && sin(_trickTime * 26) > -0.3) {
      _trickText.render(
        canvas,
        L.trick,
        Vector2(size.x / 2, 78),
        anchor: Anchor.center,
      );
    }

    final freeze = _freezePainter;
    if (freeze != null) {
      // Önce büyükten oturur, sonra yavaşça nabız gibi atar.
      final pop = 1.5 - 0.5 * min(1.0, _freezeTime / _popDuration);
      final pulse = 1 + 0.06 * sin(_freezeTime * 9);
      final fit = (size.x - 32) / freeze.width;
      canvas
        ..save()
        // Komutların yeri: portre sütunu bunun altından başlar.
        ..translate(size.x / 2, 125)
        ..scale(min(pop * pulse, fit));
      freeze.paint(canvas, Offset(-freeze.width / 2, -freeze.height / 2));
      canvas.restore();
    }

    if (_toastTime < _toastDuration && _toast.isNotEmpty) {
      // Son yarım saniyede soluklaşarak kaybolur.
      final alpha = min(1.0, (_toastDuration - _toastTime) / 0.5);
      TextPaint(
        style: TextStyle(
          fontSize: 19,
          fontWeight: FontWeight.bold,
          color: _toastColor.withValues(alpha: alpha),
          shadows: [
            Shadow(
              blurRadius: 6,
              color: Colors.black.withValues(alpha: 0.9 * alpha),
            ),
          ],
        ),
      ).render(canvas, _toast, Vector2(size.x / 2, 185), anchor: Anchor.center);
    }

    if (showPortraits) {
      _renderPortraits(canvas);
      _renderHearts(canvas, size);
    }

    // Sol üstte iki satır: bölüm adı ve süre (sağ üstteki ☰ butonuna değmesin).
    final label = levelLabel;
    final left = timeLeft;
    if (label != null && left != null) {
      final seconds = left.ceil();
      final clock =
          '${seconds ~/ 60}:${(seconds % 60).toString().padLeft(2, '0')}';
      _labelText
        ..render(canvas, label, Vector2(16, 12))
        ..render(canvas, '⏱ $clock', Vector2(16, 33));
    }
  }

  void _renderHearts(Canvas canvas, Vector2 size) {
    final image = heart;
    if (image == null) return;
    final height = _heartSize * _heartSource.height / _heartSource.width;
    for (var i = 0; i < _maxLives; i++) {
      final alive = i < _lives;
      final center = Offset(
        16 + _heartSize / 2 + i * (_heartSize + _heartGap),
        size.y - 20 - height / 2,
      );
      var scale = 1.0;
      var dx = 0.0;
      // Az önce giden can: titreyip bir an büyüyerek söner.
      if (i == _lives && _lifeLostTime < 0.6) {
        final k = _lifeLostTime / 0.6;
        dx = sin(_lifeLostTime * 50) * 5 * (1 - k);
        scale = 1 + 0.4 * (1 - k);
      }
      canvas
        ..save()
        ..translate(center.dx + dx, center.dy)
        ..scale(scale)
        ..drawImageRect(
          image,
          _heartSource,
          Rect.fromCenter(
            center: Offset.zero,
            width: _heartSize,
            height: height,
          ),
          alive ? _heartPaint : _lostHeartPaint,
        )
        ..restore();
    }
  }

  void _renderTip(Canvas canvas, Vector2 size) {
    final tip = _tip;
    if (tip == null || _tipTime < 0 || _tipTime > _tipDuration) return;
    // Dar tutulur: soldaki portrelere ve ortadaki karakterlere taşmasın.
    final maxWidth = min(size.x - 180, 230.0);
    var painter = _tipPainter;
    if (painter == null || _tipLaidOutWidth != maxWidth) {
      painter = _tipPainter = TextPainter(
        text: TextSpan(
          text: tip,
          style: const TextStyle(
            fontSize: 16,
            height: 1.25,
            fontWeight: FontWeight.w700,
            color: Colors.white,
          ),
        ),
        textAlign: TextAlign.center,
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: maxWidth);
      _tipLaidOutWidth = maxWidth;
    }
    // İlk ve son 0,3 saniyede yumuşakça belirip kaybolur.
    final alpha = min(1.0, min(_tipTime, _tipDuration - _tipTime) / 0.3);
    // Büyük yazının ve "yandı" haberinin altında, karakterlerin üstünde.
    final center = Offset(size.x / 2, 255 + painter.height / 2);
    final box = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: center,
        width: painter.width + 28,
        height: painter.height + 22,
      ),
      const Radius.circular(18),
    );
    canvas.saveLayer(null, Paint()..color = Color.fromRGBO(0, 0, 0, alpha));
    canvas
      ..drawRRect(box, _tipPaint)
      ..drawRRect(box, _tipBorder);
    painter.paint(
      canvas,
      center - Offset(painter.width / 2, painter.height / 2),
    );
    canvas.restore();
  }

  /// Ters kontrol şeridinin üstünde: "LİDER KÖR · 3" ve azalan çubuk.
  /// Süreli güç şeridi ("LİDER KÖR · 3", "KALKAN · 12"): yazı ve altında
  /// [fraction] oranında kısalan çizgi.
  void _renderTimerBanner(
    Canvas canvas,
    Offset center,
    String text,
    double fraction,
    Paint paint,
  ) {
    // Kutu yazıya göre genişler (diller arasında uzunluk çok değişiyor).
    final width = _blindText.getLineMetrics(text).width + 40;
    final box = Rect.fromCenter(center: center, width: width, height: 40);
    canvas.drawRRect(
      RRect.fromRectAndRadius(box, const Radius.circular(20)),
      paint,
    );
    _blindText.render(
      canvas,
      text,
      Vector2(center.dx, center.dy - 3),
      anchor: Anchor.center,
    );
    // Kalan süre: kutunun altında kısalan çizgi.
    final k = fraction.clamp(0.0, 1.0);
    canvas.drawRect(
      Rect.fromLTWH(box.left + 20, box.bottom - 7, (box.width - 40) * k, 3),
      Paint()..color = const Color(0xFF0E2A33),
    );
  }

  void _renderReverseBanner(Canvas canvas, Vector2 size) {
    final pulse = 0.75 + 0.25 * sin(_clock * 6);
    final text = L.controlsReversedBanner;
    final width = _reverseText.getLineMetrics(text).width + 40;
    final rect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: Offset(size.x / 2, size.y - 110),
        width: width,
        height: 46,
      ),
      const Radius.circular(23),
    );
    _reversePaint.color = reverseColor.withValues(alpha: 0.85 * pulse);
    canvas.drawRRect(rect, _reversePaint);
    _reverseText.render(
      canvas,
      text,
      Vector2(size.x / 2, size.y - 110),
      anchor: Anchor.center,
    );
  }

  /// Portrenin sağında, ona işaret eden konuşma balonu; sonunda solar.
  void _renderBubble(Canvas canvas, Rect portrait, TextPainter painter) {
    final alpha = min(1.0, (_tauntDuration - _tauntTime) / 0.4);
    final box = Rect.fromLTWH(
      portrait.right + 14,
      portrait.center.dy - painter.height / 2 - 8,
      painter.width + 20,
      painter.height + 16,
    );
    final tail = Path()
      ..moveTo(box.left, portrait.center.dy - 7)
      ..lineTo(portrait.right + 3, portrait.center.dy)
      ..lineTo(box.left, portrait.center.dy + 7)
      ..close();
    final shape = Path()
      ..addRRect(RRect.fromRectAndRadius(box, const Radius.circular(12)))
      ..addPath(tail, Offset.zero);
    canvas.saveLayer(null, Paint()..color = Color.fromRGBO(0, 0, 0, alpha));
    canvas
      ..drawPath(shape, _bubblePaint)
      ..drawPath(shape, _bubbleBorder);
    painter.paint(canvas, Offset(box.left + 10, box.top + 8));
    canvas.restore();
  }

  void _renderPortraits(Canvas canvas) {
    for (var i = 0; i < portraits.length; i++) {
      final image = portraits[i];
      final since = _eliminated[i];
      final shaking = since != null && since < _shakeDuration;
      final out = since != null && !shaking;
      // Yandığı an sağa sola titrer, titreme giderek söner.
      // Laf sokarken de titrer (sarı-pembe çerçeveyle).
      final taunting =
          i == _tauntIndex && _tauntTime < _tauntShake && since == null;
      final shake = shaking
          ? sin(since * 55) * 7 * (1 - since / _shakeDuration)
          : taunting
          ? sin(_tauntTime * 55) * 6 * (1 - _tauntTime / _tauntShake)
          : 0.0;
      final rect = Rect.fromLTWH(
        12 + shake,
        _portraitTop + i * (_portraitSize + _portraitGap),
        _portraitSize,
        _portraitSize,
      );
      final rounded = RRect.fromRectAndRadius(rect, const Radius.circular(8));

      canvas
        ..save()
        ..clipRRect(rounded)
        ..drawImageRect(
          image,
          Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble()),
          rect,
          _portraitPaint,
        );
      if (out) canvas.drawRect(rect, _portraitFade);
      canvas.restore();

      _framePaint.color = out || shaking
          ? loseColor
          : taunting
          ? reverseColor
          : frameColor;
      canvas.drawRRect(rounded, _framePaint);

      if (out) {
        final r = rect.deflate(10);
        canvas
          ..drawLine(r.topLeft, r.bottomRight, _crossPaint)
          ..drawLine(r.topRight, r.bottomLeft, _crossPaint);
      }
      final painter = _tauntPainter;
      if (i == _tauntIndex &&
          _tauntTime < _tauntDuration &&
          painter != null &&
          !out) {
        _renderBubble(canvas, rect, painter);
      }
      // İsim resmin altında: yanda olunca ortadaki yazıların üstüne biniyordu.
      if (i < portraitNames.length) {
        _nameText.render(
          canvas,
          portraitNames[i],
          Vector2(rect.center.dx, rect.bottom + 2),
          anchor: Anchor.topCenter,
        );
      }
    }
  }
}
