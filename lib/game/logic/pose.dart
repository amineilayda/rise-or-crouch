import '../l10n/strings.dart';

enum Pose {
  stand,
  crouch;

  /// Oyun kurucunun bağırdığı kelime, oyuncunun dilinde (DEVE / CÜCE).
  String get word => this == Pose.stand ? L.rise : L.crouch;

  Pose get opposite => this == Pose.stand ? Pose.crouch : Pose.stand;
}
