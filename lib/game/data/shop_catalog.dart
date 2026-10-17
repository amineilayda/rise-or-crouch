import '../l10n/strings.dart';
import 'player_profile.dart';

/// Mağazada satılan bir şey. Yeni ürün eklemek için [shopCatalog]'a bir
/// kayıt eklemek yeterli: kaç tane alındığını profilden okur, alınınca
/// profile işler.
class ShopItem {
  const ShopItem({
    required this.id,
    required this.icon,
    required this.price,
    required this.maxOwned,
    required this.owned,
    required this.grant,
  });

  final String id;

  /// dil ayarlari
  String get name => L.shopItemName(id);
  String get description => L.shopItemDescription(id);

  final String icon;
  final int price;
  final int maxOwned;
  final int Function(PlayerProfile profile) owned;

  /// satin alim sonrasi
  final Future<void> Function(PlayerProfile profile) grant;
  bool isMaxed(PlayerProfile profile) => owned(profile) >= maxOwned;
}

/// Mağazadaki ürünler:
final List<ShopItem> shopCatalog = [
  // Kalıcı: her bölüme bir can fazlasıyla başlanır.
  ShopItem(
    id: 'extra_life',
    icon: 'assets/images/icons/heart.webp',
    price: 100,
    maxOwned: 3,
    owned: (profile) => profile.extraLives.value,
    grant: (profile) => profile.addExtraLife(),
  ),
  // Tek kullanımlık: oyunda ayna butonuyla lider 4 sn kör edilir.
  ShopItem(
    id: 'blind',
    icon: 'assets/images/icons/mirror.webp',
    price: 200,
    maxOwned: 5,
    owned: (profile) => profile.blindCharges.value,
    grant: (profile) => profile.addBlindCharge(),
  ),
  // Tek kullanımlık: oyunda kalkan butonuyla 15 sn rakiplerin körleme ve
  // ters kontrolüne (ve laf sokmalarına) karşı korunulur.
  ShopItem(
    id: 'shield',
    icon: 'assets/images/icons/shield.webp',
    price: 80,
    maxOwned: 5,
    owned: (profile) => profile.shieldCharges.value,
    grant: (profile) => profile.addShieldCharge(),
  ),
];
