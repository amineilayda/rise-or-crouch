import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:rise_and_crouch/game/l10n/strings.dart';

void main() {
  test('sistem dilinden oyun dili', () {
    AppLanguage pick(List<Locale> l) => AppLanguage.fromLocales(l);
    expect(pick([const Locale('th', 'TH')]), AppLanguage.th);
    expect(pick([const Locale('id')]), AppLanguage.id);
    expect(pick([const Locale('in', 'ID')]), AppLanguage.id);
    expect(pick([const Locale('pt', 'BR')]), AppLanguage.pt);
    expect(pick([const Locale('zh', 'CN')]), AppLanguage.zh);
    expect(pick([const Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hans')]), AppLanguage.zh);
    expect(pick([const Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hant', countryCode: 'TW')]), AppLanguage.zhHant);
    expect(pick([const Locale('zh', 'HK')]), AppLanguage.zhHant);
    expect(pick([const Locale('nl'), const Locale('tr', 'TR')]), AppLanguage.tr);
    expect(pick([const Locale('nl')]), AppLanguage.en);
    expect(AppLanguage.fromName('zh'), AppLanguage.zh);
    expect(AppLanguage.fromName('zhHant'), AppLanguage.zhHant);
    expect(AppLanguage.fromName(null), isNull);
  });
}
