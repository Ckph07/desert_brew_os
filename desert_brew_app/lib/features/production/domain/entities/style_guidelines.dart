import 'dart:convert';

import 'package:equatable/equatable.dart';
import 'package:flutter/services.dart';

class NumericRange extends Equatable {
  const NumericRange(this.min, this.max);

  final double min;
  final double max;

  bool contains(double value) => value >= min && value <= max;

  double get midpoint => (min + max) / 2.0;

  String format(int decimals) =>
      '${min.toStringAsFixed(decimals)} - ${max.toStringAsFixed(decimals)}';

  @override
  List<Object?> get props => [min, max];
}

class WaterProfileTarget extends Equatable {
  const WaterProfileTarget({
    required this.ca,
    required this.mg,
    required this.na,
    required this.cl,
    required this.so4,
    required this.hco3,
  });

  final double ca;
  final double mg;
  final double na;
  final double cl;
  final double so4;
  final double hco3;

  Map<String, double> toMap() => {
    'ca': ca,
    'mg': mg,
    'na': na,
    'cl': cl,
    'so4': so4,
    'hco3': hco3,
  };

  @override
  List<Object?> get props => [ca, mg, na, cl, so4, hco3];
}

class StyleTargetSuggestion extends Equatable {
  const StyleTargetSuggestion({
    required this.expectedOg,
    required this.expectedFg,
    required this.expectedAbv,
    required this.ibu,
    required this.colorSrm,
    required this.waterProfile,
  });

  final double expectedOg;
  final double expectedFg;
  final double expectedAbv;
  final double ibu;
  final double colorSrm;
  final WaterProfileTarget waterProfile;

  @override
  List<Object?> get props => [
    expectedOg,
    expectedFg,
    expectedAbv,
    ibu,
    colorSrm,
    waterProfile,
  ];
}

class BeerStyleProfile extends Equatable {
  const BeerStyleProfile({
    required this.name,
    required this.aliases,
    required this.ogRange,
    required this.fgRange,
    required this.abvRange,
    required this.ibuRange,
    required this.srmRange,
    required this.minScaleFactor,
    required this.maxScaleFactor,
    required this.waterProfileRanges,
    required this.waterProfileTarget,
  });

  final String name;
  final List<String> aliases;
  final NumericRange ogRange;
  final NumericRange fgRange;
  final NumericRange abvRange;
  final NumericRange ibuRange;
  final NumericRange srmRange;
  final double minScaleFactor;
  final double maxScaleFactor;
  final Map<String, NumericRange> waterProfileRanges;
  final WaterProfileTarget waterProfileTarget;

  List<String> missingMetrics({
    double? expectedOg,
    double? expectedFg,
    double? expectedAbv,
    double? ibu,
  }) {
    final missing = <String>[];
    if (expectedOg == null) missing.add('OG');
    if (expectedFg == null) missing.add('FG');
    if (expectedAbv == null) missing.add('ABV');
    if (ibu == null) missing.add('IBU');
    return missing;
  }

  List<String> missingAdvancedMetrics({
    double? colorSrm,
    required Map<String, double?> waterProfile,
  }) {
    final missing = <String>[];
    if (colorSrm == null) {
      missing.add('SRM');
    }

    for (final key in BeerStyleGuidelines.waterKeys) {
      final value = waterProfile[key];
      if (value == null) {
        missing.add(key.toUpperCase());
      }
    }
    return missing;
  }

  List<String> validateRecipeTargets({
    required double expectedOg,
    required double expectedFg,
    required double expectedAbv,
    required double ibu,
    double? colorSrm,
  }) {
    final issues = <String>[];
    if (!ogRange.contains(expectedOg)) {
      issues.add(
        'OG fuera de rango para $name: ${expectedOg.toStringAsFixed(3)} '
        '(esperado ${ogRange.format(3)}).',
      );
    }
    if (!fgRange.contains(expectedFg)) {
      issues.add(
        'FG fuera de rango para $name: ${expectedFg.toStringAsFixed(3)} '
        '(esperado ${fgRange.format(3)}).',
      );
    }
    if (expectedOg <= expectedFg) {
      issues.add(
        'OG debe ser mayor que FG (OG ${expectedOg.toStringAsFixed(3)}, '
        'FG ${expectedFg.toStringAsFixed(3)}).',
      );
    }
    if (!abvRange.contains(expectedAbv)) {
      issues.add(
        'ABV fuera de rango para $name: ${expectedAbv.toStringAsFixed(1)}% '
        '(esperado ${abvRange.format(1)}%).',
      );
    }
    if (!ibuRange.contains(ibu)) {
      issues.add(
        'IBU fuera de rango para $name: ${ibu.toStringAsFixed(0)} '
        '(esperado ${ibuRange.format(0)}).',
      );
    }
    if (colorSrm != null && !srmRange.contains(colorSrm)) {
      issues.add(
        'SRM fuera de rango para $name: ${colorSrm.toStringAsFixed(1)} '
        '(esperado ${srmRange.format(1)}).',
      );
    }
    return issues;
  }

  List<String> validateBatchScale({
    required double recipeBatchSizeLiters,
    required double plannedVolumeLiters,
  }) {
    final issues = <String>[];
    if (recipeBatchSizeLiters <= 0 || plannedVolumeLiters <= 0) {
      return ['El volumen del batch debe ser mayor a 0.'];
    }

    final ratio = plannedVolumeLiters / recipeBatchSizeLiters;
    if (ratio < minScaleFactor || ratio > maxScaleFactor) {
      final minVolume = recipeBatchSizeLiters * minScaleFactor;
      final maxVolume = recipeBatchSizeLiters * maxScaleFactor;
      issues.add(
        'Volumen planificado fuera de rango para $name: '
        '${plannedVolumeLiters.toStringAsFixed(1)} L '
        '(recomendado ${minVolume.toStringAsFixed(1)} - '
        '${maxVolume.toStringAsFixed(1)} L).',
      );
    }
    return issues;
  }

  List<String> validateWaterProfile(Map<String, double> waterProfile) {
    final issues = <String>[];
    for (final key in BeerStyleGuidelines.waterKeys) {
      final value = waterProfile[key];
      final range = waterProfileRanges[key];
      if (value == null || range == null) continue;
      if (!range.contains(value)) {
        issues.add(
          '${key.toUpperCase()} fuera de rango para $name: '
          '${value.toStringAsFixed(0)} ppm '
          '(esperado ${range.format(0)} ppm).',
        );
      }
    }
    return issues;
  }

  StyleTargetSuggestion suggestTargets() {
    return StyleTargetSuggestion(
      expectedOg: ogRange.midpoint,
      expectedFg: fgRange.midpoint,
      expectedAbv: abvRange.midpoint,
      ibu: ibuRange.midpoint,
      colorSrm: srmRange.midpoint,
      waterProfile: waterProfileTarget,
    );
  }

  String rangesLabel() {
    return 'OG ${ogRange.format(3)} · FG ${fgRange.format(3)} · '
        'ABV ${abvRange.format(1)}% · IBU ${ibuRange.format(0)} · '
        'SRM ${srmRange.format(1)}';
  }

  String waterTargetLabel() {
    final t = waterProfileTarget;
    return 'Agua ppm: Ca ${t.ca.toStringAsFixed(0)}, Mg ${t.mg.toStringAsFixed(0)}, '
        'Na ${t.na.toStringAsFixed(0)}, Cl ${t.cl.toStringAsFixed(0)}, '
        'SO4 ${t.so4.toStringAsFixed(0)}, HCO3 ${t.hco3.toStringAsFixed(0)}';
  }

  @override
  List<Object?> get props => [
    name,
    aliases,
    ogRange,
    fgRange,
    abvRange,
    ibuRange,
    srmRange,
    minScaleFactor,
    maxScaleFactor,
    waterProfileRanges,
    waterProfileTarget,
  ];
}

class BeerStyleGuidelines {
  static const List<String> waterKeys = ['ca', 'mg', 'na', 'cl', 'so4', 'hco3'];
  static const String defaultAssetPath = 'assets/data/ba_beer_styles_2025.json';

  static bool _didAttemptAssetLoad = false;
  static bool _loadedFromAsset = false;

  static bool get loadedFromAsset => _loadedFromAsset;
  static List<BeerStyleProfile> get profiles => List.unmodifiable(_profiles);

  static const List<BeerStyleProfile> _fallbackProfiles = [
    BeerStyleProfile(
      name: 'American IPA',
      aliases: [
        'AMERICAN IPA',
        'WEST COAST IPA',
        'AMERICAN INDIA PALE ALE (IPA)',
        'IPA',
      ],
      ogRange: NumericRange(1.060, 1.070),
      fgRange: NumericRange(1.012, 1.018),
      abvRange: NumericRange(6.3, 7.5),
      ibuRange: NumericRange(50, 70),
      srmRange: NumericRange(6, 12),
      minScaleFactor: 0.7,
      maxScaleFactor: 1.6,
      waterProfileRanges: {
        'ca': NumericRange(100, 180),
        'mg': NumericRange(5, 20),
        'na': NumericRange(0, 60),
        'cl': NumericRange(40, 100),
        'so4': NumericRange(150, 300),
        'hco3': NumericRange(0, 100),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 130,
        mg: 12,
        na: 20,
        cl: 70,
        so4: 220,
        hco3: 50,
      ),
    ),
    BeerStyleProfile(
      name: 'Hazy IPA',
      aliases: [
        'HAZY IPA',
        'NEW ENGLAND IPA',
        'NEIPA',
        'JUICY OR HAZY INDIA PALE ALE',
      ],
      ogRange: NumericRange(1.060, 1.070),
      fgRange: NumericRange(1.012, 1.020),
      abvRange: NumericRange(6.3, 7.5),
      ibuRange: NumericRange(50, 70),
      srmRange: NumericRange(5, 10),
      minScaleFactor: 0.7,
      maxScaleFactor: 1.5,
      waterProfileRanges: {
        'ca': NumericRange(80, 150),
        'mg': NumericRange(5, 20),
        'na': NumericRange(0, 50),
        'cl': NumericRange(120, 220),
        'so4': NumericRange(40, 120),
        'hco3': NumericRange(0, 100),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 110,
        mg: 12,
        na: 20,
        cl: 170,
        so4: 80,
        hco3: 40,
      ),
    ),
    BeerStyleProfile(
      name: 'Blonde Ale',
      aliases: ['BLONDE ALE', 'GOLDEN ALE', 'BELGIAN-STYLE BLONDE ALE'],
      ogRange: NumericRange(1.038, 1.054),
      fgRange: NumericRange(1.008, 1.013),
      abvRange: NumericRange(3.8, 5.5),
      ibuRange: NumericRange(15, 25),
      srmRange: NumericRange(3, 6),
      minScaleFactor: 0.6,
      maxScaleFactor: 1.8,
      waterProfileRanges: {
        'ca': NumericRange(40, 90),
        'mg': NumericRange(5, 15),
        'na': NumericRange(0, 40),
        'cl': NumericRange(30, 80),
        'so4': NumericRange(30, 80),
        'hco3': NumericRange(0, 70),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 60,
        mg: 10,
        na: 10,
        cl: 50,
        so4: 50,
        hco3: 35,
      ),
    ),
    BeerStyleProfile(
      name: 'American Pale Ale',
      aliases: [
        'PALE ALE',
        'AMERICAN PALE ALE',
        'JUICY OR HAZY PALE ALE',
        'APA',
      ],
      ogRange: NumericRange(1.044, 1.052),
      fgRange: NumericRange(1.008, 1.016),
      abvRange: NumericRange(4.5, 5.6),
      ibuRange: NumericRange(30, 50),
      srmRange: NumericRange(4, 10),
      minScaleFactor: 0.7,
      maxScaleFactor: 1.7,
      waterProfileRanges: {
        'ca': NumericRange(60, 140),
        'mg': NumericRange(5, 20),
        'na': NumericRange(0, 50),
        'cl': NumericRange(40, 90),
        'so4': NumericRange(90, 180),
        'hco3': NumericRange(0, 100),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 95,
        mg: 12,
        na: 15,
        cl: 60,
        so4: 135,
        hco3: 50,
      ),
    ),
    BeerStyleProfile(
      name: 'Stout',
      aliases: [
        'STOUT',
        'AMERICAN STOUT',
        'IMPERIAL STOUT',
        'IRISH STOUT',
        'DRY STOUT',
      ],
      ogRange: NumericRange(1.044, 1.075),
      fgRange: NumericRange(1.010, 1.022),
      abvRange: NumericRange(4.0, 8.0),
      ibuRange: NumericRange(25, 50),
      srmRange: NumericRange(30, 45),
      minScaleFactor: 0.6,
      maxScaleFactor: 1.6,
      waterProfileRanges: {
        'ca': NumericRange(60, 140),
        'mg': NumericRange(5, 20),
        'na': NumericRange(0, 70),
        'cl': NumericRange(40, 120),
        'so4': NumericRange(40, 120),
        'hco3': NumericRange(120, 260),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 90,
        mg: 12,
        na: 25,
        cl: 85,
        so4: 70,
        hco3: 190,
      ),
    ),
    BeerStyleProfile(
      name: 'Porter',
      aliases: ['PORTER', 'AMERICAN PORTER', 'ROBUST PORTER'],
      ogRange: NumericRange(1.040, 1.065),
      fgRange: NumericRange(1.008, 1.018),
      abvRange: NumericRange(4.0, 6.5),
      ibuRange: NumericRange(18, 35),
      srmRange: NumericRange(20, 35),
      minScaleFactor: 0.6,
      maxScaleFactor: 1.6,
      waterProfileRanges: {
        'ca': NumericRange(60, 130),
        'mg': NumericRange(5, 20),
        'na': NumericRange(0, 60),
        'cl': NumericRange(40, 100),
        'so4': NumericRange(50, 130),
        'hco3': NumericRange(90, 220),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 85,
        mg: 12,
        na: 20,
        cl: 75,
        so4: 90,
        hco3: 150,
      ),
    ),
    BeerStyleProfile(
      name: 'Lager',
      aliases: [
        'LAGER',
        'AMERICAN LAGER',
        'AMERICAN LIGHT LAGER',
        'AMERICAN AMBER LAGER',
        'MEXICAN LAGER',
        'GERMAN-STYLE PILSENER',
        'BOHEMIAN-STYLE PILSENER',
        'MUNICH-STYLE HELLES',
        'GERMAN-STYLE MARZEN',
        'GERMAN-STYLE DUNKEL/MUNICH DUNKEL',
        'GERMAN-STYLE SCHWARZBIER',
        'TRADITIONAL GERMAN-STYLE BOCK',
        'GERMAN-STYLE DOPPELBOCK',
        'INDIA PALE LAGER / COLD IPA',
        'PILSNER',
      ],
      ogRange: NumericRange(1.040, 1.055),
      fgRange: NumericRange(1.006, 1.014),
      abvRange: NumericRange(4.2, 5.8),
      ibuRange: NumericRange(15, 30),
      srmRange: NumericRange(2, 6),
      minScaleFactor: 0.6,
      maxScaleFactor: 1.9,
      waterProfileRanges: {
        'ca': NumericRange(30, 90),
        'mg': NumericRange(3, 12),
        'na': NumericRange(0, 35),
        'cl': NumericRange(30, 80),
        'so4': NumericRange(25, 90),
        'hco3': NumericRange(0, 80),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 55,
        mg: 8,
        na: 10,
        cl: 50,
        so4: 45,
        hco3: 35,
      ),
    ),
    BeerStyleProfile(
      name: 'Wheat Beer',
      aliases: [
        'WHEAT',
        'HEFEWEIZEN',
        'WITBIER',
        'BELGIAN-STYLE WITBIER (WHITE BEER)',
      ],
      ogRange: NumericRange(1.044, 1.056),
      fgRange: NumericRange(1.010, 1.014),
      abvRange: NumericRange(4.3, 5.6),
      ibuRange: NumericRange(8, 20),
      srmRange: NumericRange(2, 8),
      minScaleFactor: 0.7,
      maxScaleFactor: 1.7,
      waterProfileRanges: {
        'ca': NumericRange(30, 90),
        'mg': NumericRange(3, 15),
        'na': NumericRange(0, 40),
        'cl': NumericRange(40, 110),
        'so4': NumericRange(20, 70),
        'hco3': NumericRange(0, 90),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 55,
        mg: 10,
        na: 15,
        cl: 75,
        so4: 40,
        hco3: 45,
      ),
    ),
    BeerStyleProfile(
      name: 'Belgian Tripel',
      aliases: ['TRIPEL', 'BELGIAN TRIPEL', 'BELGIAN-STYLE TRIPEL'],
      ogRange: NumericRange(1.070, 1.092),
      fgRange: NumericRange(1.008, 1.018),
      abvRange: NumericRange(7.1, 10.1),
      ibuRange: NumericRange(20, 45),
      srmRange: NumericRange(4, 7),
      minScaleFactor: 0.7,
      maxScaleFactor: 1.4,
      waterProfileRanges: {
        'ca': NumericRange(40, 110),
        'mg': NumericRange(5, 15),
        'na': NumericRange(0, 45),
        'cl': NumericRange(40, 110),
        'so4': NumericRange(30, 90),
        'hco3': NumericRange(0, 100),
      },
      waterProfileTarget: WaterProfileTarget(
        ca: 70,
        mg: 10,
        na: 15,
        cl: 70,
        so4: 55,
        hco3: 45,
      ),
    ),
  ];

  static List<BeerStyleProfile> _profiles = List<BeerStyleProfile>.from(
    _fallbackProfiles,
  );
  static final Map<String, BeerStyleProfile> _fallbackByName = {
    for (final profile in _fallbackProfiles) profile.name: profile,
  };

  static Future<void> initialize({
    AssetBundle? bundle,
    String assetPath = defaultAssetPath,
    bool forceReload = false,
  }) async {
    if (_didAttemptAssetLoad && !forceReload) {
      return;
    }
    _didAttemptAssetLoad = true;

    try {
      final sourceBundle = bundle ?? rootBundle;
      final raw = await sourceBundle.loadString(assetPath);
      final runtimeProfiles = _profilesFromCatalogJson(raw);
      if (runtimeProfiles.isNotEmpty) {
        _profiles = runtimeProfiles;
        _loadedFromAsset = true;
      } else {
        _profiles = List<BeerStyleProfile>.from(_fallbackProfiles);
        _loadedFromAsset = false;
      }
    } catch (_) {
      _profiles = List<BeerStyleProfile>.from(_fallbackProfiles);
      _loadedFromAsset = false;
    }
  }

  static void resetForTesting() {
    _didAttemptAssetLoad = false;
    _loadedFromAsset = false;
    _profiles = List<BeerStyleProfile>.from(_fallbackProfiles);
  }

  static void overrideProfilesForTesting(List<BeerStyleProfile> profiles) {
    _didAttemptAssetLoad = true;
    _loadedFromAsset = false;
    _profiles = List<BeerStyleProfile>.from(profiles);
  }

  static BeerStyleProfile? match(String? rawStyle) {
    final style = _normalize(rawStyle);
    if (style.isEmpty) return null;

    BeerStyleProfile? bestMatch;
    var bestScore = -1;

    for (final profile in profiles) {
      for (final alias in profile.aliases) {
        final normalizedAlias = _normalize(alias);
        if (normalizedAlias.isEmpty) continue;

        var score = -1;
        if (style == normalizedAlias) {
          score = 300 + normalizedAlias.length;
        } else if (style.contains(normalizedAlias)) {
          score = 200 + normalizedAlias.length;
        } else if (normalizedAlias.contains(style)) {
          score = 100 + style.length;
        }

        if (score > bestScore) {
          bestScore = score;
          bestMatch = profile;
        }
      }
    }
    return bestMatch;
  }

  static List<BeerStyleProfile> _profilesFromCatalogJson(String rawJson) {
    final decoded = json.decode(rawJson);
    if (decoded is! Map<String, dynamic>) {
      return const [];
    }

    final rows = decoded['styles'];
    if (rows is! List) {
      return const [];
    }

    final runtimeProfiles = <BeerStyleProfile>[];
    final runtimeNames = <String>{};
    for (final item in rows) {
      if (item is! Map) {
        continue;
      }
      final row = Map<String, dynamic>.from(item);
      final profile = _profileFromCatalogRow(row);
      if (profile == null) {
        continue;
      }
      final key = _normalize(profile.name);
      if (runtimeNames.add(key)) {
        runtimeProfiles.add(profile);
      }
    }

    if (runtimeProfiles.isEmpty) {
      return const [];
    }

    final merged = List<BeerStyleProfile>.from(runtimeProfiles);
    final mergedKeys = runtimeProfiles.map((p) => _normalize(p.name)).toSet();
    for (final fallback in _fallbackProfiles) {
      final key = _normalize(fallback.name);
      if (mergedKeys.add(key)) {
        merged.add(fallback);
      }
    }
    return merged;
  }

  static BeerStyleProfile? _profileFromCatalogRow(Map<String, dynamic> row) {
    final name = (row['name'] as String?)?.trim();
    if (name == null || name.isEmpty) {
      return null;
    }

    final ogMin = _toDouble(row['og_min']);
    final ogMax = _toDouble(row['og_max']);
    final fgMin = _toDouble(row['fg_min']);
    final fgMax = _toDouble(row['fg_max']);
    final abvMin = _toDouble(row['abv_min']);
    final abvMax = _toDouble(row['abv_max']);
    final ibuMin = _toDouble(row['ibu_min']);
    final ibuMax = _toDouble(row['ibu_max']);
    final srmMin = _toDouble(row['srm_min']);
    final srmMax = _toDouble(row['srm_max']);

    // Skip styles with non-numeric ranges (for example "Varies with style").
    if (ogMin == null ||
        ogMax == null ||
        fgMin == null ||
        fgMax == null ||
        abvMin == null ||
        abvMax == null ||
        ibuMin == null ||
        ibuMax == null ||
        srmMin == null ||
        srmMax == null) {
      return null;
    }

    if (ogMin > ogMax ||
        fgMin > fgMax ||
        abvMin > abvMax ||
        ibuMin > ibuMax ||
        srmMin > srmMax) {
      return null;
    }

    final archetype = _archetypeForStyle(name);
    return BeerStyleProfile(
      name: name,
      aliases: _aliasesForStyle(name),
      ogRange: NumericRange(ogMin, ogMax),
      fgRange: NumericRange(fgMin, fgMax),
      abvRange: NumericRange(abvMin, abvMax),
      ibuRange: NumericRange(ibuMin, ibuMax),
      srmRange: NumericRange(srmMin, srmMax),
      minScaleFactor: archetype.minScaleFactor,
      maxScaleFactor: archetype.maxScaleFactor,
      waterProfileRanges: Map<String, NumericRange>.from(
        archetype.waterProfileRanges,
      ),
      waterProfileTarget: archetype.waterProfileTarget,
    );
  }

  static List<String> _aliasesForStyle(String styleName) {
    final style = _normalize(styleName);
    final aliases = <String>{styleName.toUpperCase()};

    if (style == 'AMERICAN STYLE INDIA PALE ALE') {
      aliases.addAll(const ['AMERICAN IPA', 'WEST COAST IPA', 'IPA']);
    }
    if (style == 'JUICY OR HAZY INDIA PALE ALE') {
      aliases.addAll(const ['HAZY IPA', 'NEW ENGLAND IPA', 'NEIPA']);
    }
    if (style == 'GOLDEN OR BLONDE ALE') {
      aliases.addAll(const ['BLONDE ALE', 'GOLDEN ALE']);
    }
    if (style == 'SESSION INDIA PALE ALE') {
      aliases.add('SESSION IPA');
    }
    if (style == 'AMERICAN STYLE PALE ALE') {
      aliases.add('APA');
    }
    if (style.contains('WITBIER')) {
      aliases.addAll(const ['WITBIER', 'WHEAT BEER']);
    }
    if (style.contains('TRIPEL')) {
      aliases.addAll(const ['BELGIAN TRIPEL', 'TRIPEL']);
    }
    if (style.contains('WEST COAST STYLE INDIA PALE ALE')) {
      aliases.add('WEST COAST IPA');
    }
    if (style.contains('GERMAN STYLE MAERZEN')) {
      aliases.addAll(const ['GERMAN-STYLE MARZEN', 'GERMAN-STYLE MÄRZEN']);
    }
    return aliases.toList(growable: false);
  }

  static BeerStyleProfile _archetypeForStyle(String styleName) {
    final style = _normalize(styleName);

    if (style.contains('JUICY') &&
        style.contains('HAZY') &&
        style.contains('INDIA PALE ALE')) {
      return _getFallback('Hazy IPA');
    }
    if (style.contains('TRIPEL')) {
      return _getFallback('Belgian Tripel');
    }
    if (_containsAny(style, const ['WITBIER', 'WEIZEN', 'WHEAT', 'GOSE'])) {
      return _getFallback('Wheat Beer');
    }
    if (style.contains('STOUT')) {
      return _getFallback('Stout');
    }
    if (style.contains('PORTER')) {
      return _getFallback('Porter');
    }
    if (_containsAny(style, const ['BLONDE', 'GOLDEN'])) {
      return _getFallback('Blonde Ale');
    }
    if (_containsAny(style, const ['INDIA PALE ALE', ' IPA', 'IPA'])) {
      if (_containsAny(style, const ['JUICY', 'HAZY', 'NEIPA'])) {
        return _getFallback('Hazy IPA');
      }
      return _getFallback('American IPA');
    }
    if (style.contains('PALE ALE')) {
      return _getFallback('American Pale Ale');
    }
    if (_containsAny(style, const [
      'LAGER',
      'PILS',
      'BOCK',
      'MARZEN',
      'MÄRZEN',
      'DUNKEL',
      'HELLES',
      'SCHWARZBIER',
      'OKTOBERFEST',
    ])) {
      return _getFallback('Lager');
    }
    return _getFallback('American Pale Ale');
  }

  static BeerStyleProfile _getFallback(String name) =>
      _fallbackByName[name] ?? _fallbackProfiles.first;

  static bool _containsAny(String value, List<String> terms) {
    for (final term in terms) {
      if (value.contains(term)) {
        return true;
      }
    }
    return false;
  }

  static double? _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }
    return null;
  }

  static String _normalize(String? value) {
    if (value == null) return '';
    final upper = value.trim().toUpperCase();
    final deaccented = upper
        .replaceAll('Á', 'A')
        .replaceAll('À', 'A')
        .replaceAll('Â', 'A')
        .replaceAll('Ä', 'A')
        .replaceAll('Ã', 'A')
        .replaceAll('É', 'E')
        .replaceAll('È', 'E')
        .replaceAll('Ê', 'E')
        .replaceAll('Ë', 'E')
        .replaceAll('Í', 'I')
        .replaceAll('Ì', 'I')
        .replaceAll('Î', 'I')
        .replaceAll('Ï', 'I')
        .replaceAll('Ó', 'O')
        .replaceAll('Ò', 'O')
        .replaceAll('Ô', 'O')
        .replaceAll('Ö', 'O')
        .replaceAll('Õ', 'O')
        .replaceAll('Ú', 'U')
        .replaceAll('Ù', 'U')
        .replaceAll('Û', 'U')
        .replaceAll('Ü', 'U')
        .replaceAll('Ñ', 'N')
        .replaceAll('Ç', 'C');
    return deaccented.replaceAll(RegExp(r'[^A-Z0-9]+'), ' ').trim();
  }
}
