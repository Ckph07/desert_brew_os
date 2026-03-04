import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Desert Brew OS brand colors.
///
/// Warm desert tones: amber, terracotta, dark brew, and cream.
class DesertBrewColors {
  DesertBrewColors._();

  // Primary palette — Amber/Gold (beer inspired)
  static const Color primary = Color(0xFFD4A017);
  static const Color primaryLight = Color(0xFFE8C547);
  static const Color primaryDark = Color(0xFFA07B00);

  // Secondary palette — Dark Brew
  static const Color secondary = Color(0xFF2C1810);
  static const Color secondaryLight = Color(0xFF4A3228);
  static const Color secondaryDark = Color(0xFF1A0E08);

  // Accent — Terracotta Desert
  static const Color accent = Color(0xFFCC5A36);
  static const Color accentLight = Color(0xFFE07A56);
  static const Color accentDark = Color(0xFF993D1F);

  // Surface / Background
  static const Color surface = Color(0xFF1E1E2E);
  static const Color surfaceVariant = Color(0xFF2A2A3C);
  static const Color background = Color(0xFF141420);
  static const Color card = Color(0xFF252538);

  // Text
  static const Color textPrimary = Color(0xFFF5F0E8);
  static const Color textSecondary = Color(0xFFB0A898);
  static const Color textHint = Color(0xFF706858);

  // Semantic
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFFA726);
  static const Color error = Color(0xFFEF5350);
  static const Color info = Color(0xFF42A5F5);

  // Batch State Colors
  static const Color planned = Color(0xFF90A4AE);
  static const Color brewing = Color(0xFFFF8A65);
  static const Color fermenting = Color(0xFFFFD54F);
  static const Color conditioning = Color(0xFF81C784);
  static const Color packaging = Color(0xFF64B5F6);
  static const Color completed = Color(0xFF4CAF50);

  // Keg State Colors
  static const Color kegEmpty = Color(0xFF757575);
  static const Color kegClean = Color(0xFF81D4FA);
  static const Color kegFull = Color(0xFF66BB6A);
  static const Color kegTapped = Color(0xFFFFA726);
  static const Color kegInClient = Color(0xFFEF5350);
  static const Color kegQuarantine = Color(0xFFAB47BC);
}

/// Desert Brew OS Theme — Dark mode with warm amber accents.
class AppTheme {
  AppTheme._();

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.dark(
        primary: DesertBrewColors.primary,
        onPrimary: DesertBrewColors.secondaryDark,
        secondary: DesertBrewColors.accent,
        onSecondary: Colors.white,
        surface: DesertBrewColors.surface,
        onSurface: DesertBrewColors.textPrimary,
        error: DesertBrewColors.error,
      ),
      scaffoldBackgroundColor: DesertBrewColors.background,
      textTheme: GoogleFonts.outfitTextTheme(
        ThemeData.dark().textTheme,
      ).apply(
        bodyColor: DesertBrewColors.textPrimary,
        displayColor: DesertBrewColors.textPrimary,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: DesertBrewColors.surface,
        foregroundColor: DesertBrewColors.textPrimary,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.outfit(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: DesertBrewColors.textPrimary,
        ),
      ),
      cardTheme: CardTheme(
        color: DesertBrewColors.card,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: DesertBrewColors.surfaceVariant,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(
            color: DesertBrewColors.primary,
            width: 2,
          ),
        ),
        labelStyle: const TextStyle(color: DesertBrewColors.textSecondary),
        hintStyle: const TextStyle(color: DesertBrewColors.textHint),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: DesertBrewColors.primary,
          foregroundColor: DesertBrewColors.secondaryDark,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.outfit(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: DesertBrewColors.primary,
        foregroundColor: DesertBrewColors.secondaryDark,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: DesertBrewColors.surface,
        selectedItemColor: DesertBrewColors.primary,
        unselectedItemColor: DesertBrewColors.textHint,
      ),
      dividerTheme: const DividerThemeData(
        color: DesertBrewColors.surfaceVariant,
        thickness: 1,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: DesertBrewColors.surfaceVariant,
        selectedColor: DesertBrewColors.primaryDark,
        labelStyle: const TextStyle(color: DesertBrewColors.textPrimary),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}
