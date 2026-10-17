import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Menü yazılarının rengi ve fontu.
const Color menuGreen = Color(0xFF8BE04E);
const Color menuGreenDark = Color(0xFF1F4D12);
const Color menuPanel = Color(0xD9142410);

/// Koyu yeşil kontur: yazı her arka planda okunsun diye dört yöne gölge.
const List<Shadow> menuOutline = [
  Shadow(offset: Offset(2, 2), color: menuGreenDark),
  Shadow(offset: Offset(-2, 2), color: menuGreenDark),
  Shadow(offset: Offset(2, -2), color: menuGreenDark),
  Shadow(offset: Offset(-2, -2), color: menuGreenDark),
  Shadow(offset: Offset(0, 4), blurRadius: 8, color: Colors.black54),
];

TextStyle menuFont(
  double size, {
  Color color = menuGreen,
  List<Shadow>? shadows,
}) => GoogleFonts.lilitaOne(fontSize: size, color: color, shadows: shadows);
