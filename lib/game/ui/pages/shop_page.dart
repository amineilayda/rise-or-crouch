import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../data/shop_catalog.dart';
import '../../l10n/strings.dart';
import '../../viewmodel/shop_view_model.dart';
import '../theme.dart';
import '../widgets/buttons.dart';

/// Mağaza: ürün kartları (resim, ad, açıklama, sahip olunan, fiyat). Bütün
/// kurallar ve satın alma [ShopViewModel]'de; bu sayfa yalnızca çizer.
class ShopPage extends StatelessWidget {
  const ShopPage({super.key, required this.shop, required this.onBack});

  final ShopViewModel shop;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: shop,
      builder: (context, _) => SizedBox(
        width: double.infinity,
        child: Column(
          children: [
            const SizedBox(height: 24),
            Text(L.shop, style: menuFont(48, shadows: menuOutline)),
            const SizedBox(height: 24),
            for (final item in shop.items) ...[
              _ShopItemCard(item: item, shop: shop),
              const SizedBox(height: 14),
            ],
            const SizedBox(height: 4),
            // Son satın almanın sonucu (birkaç saniye görünür).
            SizedBox(
              height: 28,
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                child: Text(
                  shop.message ?? '',
                  key: ValueKey(shop.message),
                  style: GoogleFonts.quicksand(
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                    shadows: const [
                      Shadow(blurRadius: 6, color: Colors.black87),
                    ],
                  ),
                ),
              ),
            ),
            const Spacer(),
            MenuButton(
              label: L.back,
              icon: Icons.arrow_back_rounded,
              onPressed: onBack,
            ),
          ],
        ),
      ),
    );
  }
}

class _ShopItemCard extends StatelessWidget {
  const _ShopItemCard({required this.item, required this.shop});

  final ShopItem item;
  final ShopViewModel shop;

  @override
  Widget build(BuildContext context) {
    final maxed = shop.isMaxed(item);
    final canBuy = shop.canBuy(item);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: menuPanel,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: menuGreen, width: 3),
      ),
      child: Row(
        children: [
          // Resimler büyük; bellekte küçük açılsın.
          Image.asset(
            item.icon,
            width: 56,
            height: 56,
            cacheWidth: 128,
            fit: BoxFit.contain,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name, style: menuFont(22)),
                const SizedBox(height: 2),
                Text(
                  item.description,
                  style: GoogleFonts.quicksand(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  L.owned(shop.owned(item), item.maxOwned),
                  style: GoogleFonts.quicksand(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: menuGreen,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 84,
            height: 44,
            child: FilledButton(
              onPressed: canBuy ? () => shop.buy(item) : null,
              style: FilledButton.styleFrom(
                padding: EdgeInsets.zero,
                backgroundColor: const Color(0xFFFFC83A),
                foregroundColor: const Color(0xFF3A2A00),
                disabledBackgroundColor: const Color(0x667A8574),
                disabledForegroundColor: const Color(0xFFB8C0B4),
              ),
              child: maxed
                  ? Text(
                      L.maxed,
                      style: menuFont(18, color: const Color(0xFFB8C0B4)),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.monetization_on_rounded, size: 18),
                        const SizedBox(width: 4),
                        Text(
                          '${item.price}',
                          style: menuFont(
                            18,
                            color: canBuy
                                ? const Color(0xFF3A2A00)
                                : const Color(0xFFB8C0B4),
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
