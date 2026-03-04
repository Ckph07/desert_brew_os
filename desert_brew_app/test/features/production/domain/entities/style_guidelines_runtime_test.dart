import 'dart:convert';

import 'package:desert_brew_app/features/production/domain/entities/style_guidelines.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

class _InMemoryAssetBundle extends CachingAssetBundle {
  _InMemoryAssetBundle(this._assets);

  final Map<String, String> _assets;

  @override
  Future<ByteData> load(String key) async {
    final value = _assets[key];
    if (value == null) {
      throw Exception('Asset not found: $key');
    }
    final bytes = Uint8List.fromList(utf8.encode(value));
    return ByteData.view(bytes.buffer);
  }

  @override
  Future<String> loadString(String key, {bool cache = true}) async {
    final value = _assets[key];
    if (value == null) {
      throw Exception('Asset not found: $key');
    }
    return value;
  }
}

void main() {
  setUp(BeerStyleGuidelines.resetForTesting);
  tearDown(BeerStyleGuidelines.resetForTesting);

  test(
    'initialize loads style catalog from runtime JSON and matches BA style names',
    () async {
      final catalogJson = jsonEncode({
        'styles': [
          {
            'name': 'American-Style India Pale Ale',
            'og_min': 1.060,
            'og_max': 1.070,
            'fg_min': 1.010,
            'fg_max': 1.016,
            'abv_min': 6.3,
            'abv_max': 7.5,
            'ibu_min': 50,
            'ibu_max': 70,
            'srm_min': 4,
            'srm_max': 12,
          },
          {
            'name': 'Juicy or Hazy India Pale Ale',
            'og_min': 1.060,
            'og_max': 1.070,
            'fg_min': 1.008,
            'fg_max': 1.020,
            'abv_min': 6.3,
            'abv_max': 7.5,
            'ibu_min': 20,
            'ibu_max': 50,
            'srm_min': 3,
            'srm_max': 7,
          },
        ],
      });
      final bundle = _InMemoryAssetBundle({
        BeerStyleGuidelines.defaultAssetPath: catalogJson,
      });

      await BeerStyleGuidelines.initialize(bundle: bundle, forceReload: true);

      expect(BeerStyleGuidelines.loadedFromAsset, isTrue);
      final ipa = BeerStyleGuidelines.match('American-Style India Pale Ale');
      expect(ipa, isNotNull);
      expect(ipa!.name, 'American-Style India Pale Ale');
      expect(ipa.ibuRange.min, closeTo(50, 0.0001));

      final hazy = BeerStyleGuidelines.match('Hazy IPA');
      expect(hazy, isNotNull);
      expect(hazy!.name, 'Juicy or Hazy India Pale Ale');
    },
  );

  test(
    'initialize falls back to canonical profiles when asset is missing',
    () async {
      await BeerStyleGuidelines.initialize(
        bundle: _InMemoryAssetBundle(const {}),
        forceReload: true,
      );

      expect(BeerStyleGuidelines.loadedFromAsset, isFalse);
      final fallback = BeerStyleGuidelines.match('West Coast IPA');
      expect(fallback, isNotNull);
      expect(fallback!.name, 'American IPA');
    },
  );
}
