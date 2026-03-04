import 'package:flutter_test/flutter_test.dart';
import 'package:desert_brew_app/features/production/domain/entities/style_guidelines.dart';

void main() {
  setUp(BeerStyleGuidelines.resetForTesting);
  tearDown(BeerStyleGuidelines.resetForTesting);

  test('BeerStyleGuidelines matches known styles by alias', () {
    final ipa = BeerStyleGuidelines.match('West Coast IPA');
    final lager = BeerStyleGuidelines.match('Mexican Lager');

    expect(ipa, isNotNull);
    expect(ipa!.name, 'American IPA');
    expect(lager, isNotNull);
    expect(lager!.name, 'Lager');
  });

  test('BeerStyleGuidelines matches Brewers Association style names', () {
    final americanIpa = BeerStyleGuidelines.match(
      'American India Pale Ale (IPA)',
    );
    final hazyIpa = BeerStyleGuidelines.match('Juicy or Hazy India Pale Ale');
    final witbier = BeerStyleGuidelines.match(
      'Belgian-Style Witbier (White Beer)',
    );
    final tripel = BeerStyleGuidelines.match('Belgian-Style Tripel');
    final marzen = BeerStyleGuidelines.match('German-Style Märzen');

    expect(americanIpa, isNotNull);
    expect(americanIpa!.name, 'American IPA');
    expect(hazyIpa, isNotNull);
    expect(hazyIpa!.name, 'Hazy IPA');
    expect(witbier, isNotNull);
    expect(witbier!.name, 'Wheat Beer');
    expect(tripel, isNotNull);
    expect(tripel!.name, 'Belgian Tripel');
    expect(marzen, isNotNull);
    expect(marzen!.name, 'Lager');
  });

  test('BeerStyleProfile validates out-of-range recipe targets', () {
    final profile = BeerStyleGuidelines.match('American IPA')!;
    final issues = profile.validateRecipeTargets(
      expectedOg: 1.030,
      expectedFg: 1.025,
      expectedAbv: 2.2,
      ibu: 12,
    );

    expect(issues, isNotEmpty);
    expect(issues.first, contains('OG fuera de rango'));
  });

  test('BeerStyleProfile validates planned volume scale for batches', () {
    final profile = BeerStyleGuidelines.match('Belgian Tripel')!;
    final issues = profile.validateBatchScale(
      recipeBatchSizeLiters: 20,
      plannedVolumeLiters: 40,
    );

    expect(issues, isNotEmpty);
    expect(issues.first, contains('Volumen planificado fuera de rango'));
  });

  test('BeerStyleProfile validates advanced metrics (SRM + water profile)', () {
    final profile = BeerStyleGuidelines.match('American IPA')!;
    final missing = profile.missingAdvancedMetrics(
      colorSrm: null,
      waterProfile: const {
        'ca': null,
        'mg': null,
        'na': null,
        'cl': null,
        'so4': null,
        'hco3': null,
      },
    );
    expect(missing, contains('SRM'));
    expect(missing, contains('CA'));

    final waterIssues = profile.validateWaterProfile({
      'ca': 20,
      'mg': 2,
      'na': 5,
      'cl': 20,
      'so4': 30,
      'hco3': 300,
    });
    expect(waterIssues, isNotEmpty);
    expect(waterIssues.first, contains('CA fuera de rango'));
  });

  test('BeerStyleProfile suggests automatic targets', () {
    final profile = BeerStyleGuidelines.match('Hazy IPA')!;
    final suggestion = profile.suggestTargets();

    expect(suggestion.expectedOg, closeTo(profile.ogRange.midpoint, 0.0001));
    expect(suggestion.expectedFg, closeTo(profile.fgRange.midpoint, 0.0001));
    expect(suggestion.expectedAbv, closeTo(profile.abvRange.midpoint, 0.0001));
    expect(suggestion.ibu, closeTo(profile.ibuRange.midpoint, 0.0001));
    expect(suggestion.colorSrm, closeTo(profile.srmRange.midpoint, 0.0001));
    expect(suggestion.waterProfile.cl, closeTo(170, 0.0001));
  });
}
