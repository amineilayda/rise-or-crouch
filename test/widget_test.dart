import 'package:flutter_test/flutter_test.dart';
import 'package:rise_and_crouch/game/level_design/levels.dart';

void main() {
  test(
    '9 bölüm sırayla numaralı ve son bölüm ilkinden daha uzun, hızlı ve zor',
    () {
      expect(levels.length, 9);
      for (var i = 0; i < levels.length; i++) {
        expect(levels[i].number, i + 1);
      }
      final first = levels.first;
      final last = levels.last;
      expect(last.duration, greaterThan(first.duration));
      expect(last.commandInterval, lessThan(first.commandInterval));
      expect(last.reactionTime, lessThan(first.reactionTime));
      expect(last.trickChance, greaterThan(first.trickChance));
    },
  );

  test('bölümler kısalmaz ve komutlar yavaşlamaz', () {
    for (var i = 1; i < levels.length; i++) {
      expect(levels[i].duration, greaterThanOrEqualTo(levels[i - 1].duration));
      expect(
        levels[i].commandInterval,
        lessThanOrEqualTo(levels[i - 1].commandInterval),
      );
    }
  });

  test('her bölüm flame_3d ışık sınırının içinde', () {
    for (final level in levels) {
      expect(level.lights.length, lessThanOrEqualTo(8));
    }
  });

  group('eleme planı (sırada oyuncu dışında 5 kişi)', () {
    const npcCount = 5;

    test('ilk 3 bölümde kimse elenmez', () {
      for (var i = 0; i <= 3; i++) {
        expect(eliminatedBefore(i, npcCount: npcCount), (0, 0));
      }
      for (final level in levels.take(3)) {
        expect(level.eliminations, (0, 0));
      }
    });

    test('son bölüme yanında 1 ya da 2 kişiyle girilir', () {
      final (low, high) = eliminatedBefore(
        levels.length - 1,
        npcCount: npcCount,
      );
      expect(npcCount - high, greaterThanOrEqualTo(1));
      expect(npcCount - low, lessThanOrEqualTo(2));
    });

    test('yalnızca son bölümde herkes elenip oyuncu tek kalır', () {
      expect(levels.last.lastOneStanding, isTrue);
      for (final level in levels.take(levels.length - 1)) {
        expect(level.lastOneStanding, isFalse);
      }
    });
  });
}
