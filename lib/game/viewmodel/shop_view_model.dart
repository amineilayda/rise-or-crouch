import 'package:flutter/foundation.dart';

import '../data/player_profile.dart';
import '../data/shop_catalog.dart';
import '../l10n/strings.dart';

/// Satın alma sonucu; arayüz buna göre mesaj gösterir.
enum PurchaseResult { bought, notEnoughCoins, maxed }

/// Mağaza ekranının ViewModel'i: ürünleri, altını ve satın almayı yönetir.
/// Mağaza arayüzü yalnızca bunu dinler; profile doğrudan dokunmaz.
class ShopViewModel extends ChangeNotifier {
  ShopViewModel(this._profile) {
    _profile.coins.addListener(notifyListeners);
    _profile.extraLives.addListener(notifyListeners);
    _profile.blindCharges.addListener(notifyListeners);
    _profile.shieldCharges.addListener(notifyListeners);
  }

  final PlayerProfile _profile;

  List<ShopItem> get items => shopCatalog;
  int get coins => _profile.coins.value;
  int owned(ShopItem item) => item.owned(_profile);
  bool isMaxed(ShopItem item) => item.isMaxed(_profile);
  bool canBuy(ShopItem item) => !isMaxed(item) && coins >= item.price;

  /// Son satın almanın sonucu için kısa mesaj (birkaç saniye görünür).
  String? message;

  Future<PurchaseResult> buy(ShopItem item) async {
    final PurchaseResult result;
    if (isMaxed(item)) {
      result = PurchaseResult.maxed;
    } else if (!await _profile.spendCoins(item.price)) {
      result = PurchaseResult.notEnoughCoins;
    } else {
      await item.grant(_profile);
      result = PurchaseResult.bought;
    }
    _showMessage(switch (result) {
      PurchaseResult.bought => L.bought(item.name),
      PurchaseResult.notEnoughCoins => L.notEnoughCoins,
      PurchaseResult.maxed => L.limitReached(item.name),
    });
    return result;
  }

  int _messageId = 0;

  void _showMessage(String text) {
    message = text;
    final id = ++_messageId;
    notifyListeners();
    Future.delayed(const Duration(seconds: 2), () {
      if (id != _messageId) return; // arada yeni mesaj geldi
      message = null;
      notifyListeners();
    });
  }

  @override
  void dispose() {
    _profile.coins.removeListener(notifyListeners);
    _profile.extraLives.removeListener(notifyListeners);
    _profile.blindCharges.removeListener(notifyListeners);
    _profile.shieldCharges.removeListener(notifyListeners);
    super.dispose();
  }
}
