import 'package:flutter/material.dart';

import '../../l10n/strings.dart';
import '../widgets/buttons.dart';

/// Alt kısımda sonuç kartı: başlık, açıklama, ana buton ve "Ana Menü".
class ResultCard extends StatelessWidget {
  const ResultCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.primaryLabel,
    required this.onPrimary,
    required this.onMenu,
  });

  final String title;
  final String subtitle;
  final String primaryLabel;
  final VoidCallback onPrimary;
  final VoidCallback onMenu;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Align(
        alignment: Alignment.bottomCenter,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 20),
                  BigButton(label: primaryLabel, onPressed: onPrimary),
                  const SizedBox(height: 8),
                  TextButton(onPressed: onMenu, child: Text(L.mainMenu)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
