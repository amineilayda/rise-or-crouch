import 'package:flutter/material.dart';

import '../theme.dart';

/// Sol üstte altın sayısı (mağazada harcanacak).
class CoinBadge extends StatelessWidget {
  const CoinBadge({super.key, required this.coins});

  final int coins;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: menuPanel,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: menuGreen, width: 2),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.monetization_on_rounded,
            color: Color(0xFFFFC83A),
            size: 24,
          ),
          const SizedBox(width: 6),
          Text('$coins', style: menuFont(22)),
        ],
      ),
    );
  }
}
