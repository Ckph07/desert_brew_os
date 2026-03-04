import 'package:equatable/equatable.dart';

/// Recipe ingredient types
class RecipeFermentable extends Equatable {
  const RecipeFermentable({
    required this.name,
    required this.amountKg,
    this.sku,
    this.colorSrm,
    this.type,
  });
  final String name;
  final double amountKg;
  final String? sku;
  final double? colorSrm;
  final String? type;

  factory RecipeFermentable.fromJson(Map<String, dynamic> j) =>
      RecipeFermentable(
        name: j['name'] as String,
        amountKg: (j['amount_kg'] as num).toDouble(),
        sku: j['sku'] as String?,
        colorSrm: (j['color_srm'] as num?)?.toDouble(),
        type: j['type'] as String?,
      );

  @override
  List<Object?> get props => [name, amountKg, sku, colorSrm, type];
}

class RecipeHop extends Equatable {
  const RecipeHop({
    required this.name,
    required this.amountG,
    this.sku,
    this.timeMim,
    this.use,
    this.alphaAcid,
  });
  final String name;
  final double amountG;
  final String? sku;
  final double? timeMim;
  final String? use;
  final double? alphaAcid;

  factory RecipeHop.fromJson(Map<String, dynamic> j) => RecipeHop(
    name: j['name'] as String,
    amountG: (j['amount_g'] as num).toDouble(),
    sku: j['sku'] as String?,
    timeMim: (j['time_min'] as num?)?.toDouble(),
    use: j['use'] as String?,
    alphaAcid: (j['alpha_acid'] as num?)?.toDouble(),
  );

  @override
  List<Object?> get props => [name, amountG, sku, timeMim, use, alphaAcid];
}

class MashStep extends Equatable {
  const MashStep({
    required this.step,
    required this.tempC,
    required this.timeMin,
  });
  final String step;
  final double tempC;
  final double timeMin;

  factory MashStep.fromJson(Map<String, dynamic> j) => MashStep(
    step: j['step'] as String,
    tempC: (j['temp_c'] as num).toDouble(),
    timeMin: (j['time_min'] as num).toDouble(),
  );

  @override
  List<Object?> get props => [step, tempC, timeMin];
}

/// Full recipe domain entity.
class Recipe extends Equatable {
  const Recipe({
    required this.id,
    required this.name,
    required this.batchSizeLiters,
    required this.fermentables,
    required this.hops,
    required this.importedAt,
    this.style,
    this.brewer,
    this.yeast = const [],
    this.mashSteps = const [],
    this.waterProfile,
    this.expectedOg,
    this.expectedFg,
    this.expectedAbv,
    this.ibu,
    this.colorSrm,
    this.brewhouseEfficiency,
    this.notes,
  });

  final int id;
  final String name;
  final double batchSizeLiters;
  final List<RecipeFermentable> fermentables;
  final List<RecipeHop> hops;
  final DateTime importedAt;
  final String? style;
  final String? brewer;
  final List<Map<String, dynamic>> yeast;
  final List<MashStep> mashSteps;
  final Map<String, dynamic>? waterProfile;
  final double? expectedOg;
  final double? expectedFg;
  final double? expectedAbv;
  final double? ibu;
  final double? colorSrm;
  final double? brewhouseEfficiency;
  final String? notes;

  double get totalFermentablesKg =>
      fermentables.fold(0, (s, f) => s + f.amountKg);
  double get totalHopsG => hops.fold(0, (s, h) => s + h.amountG);

  @override
  List<Object?> get props => [id, name, batchSizeLiters];
}

/// Payload for creating a recipe manually.
class RecipeDraft extends Equatable {
  const RecipeDraft({
    required this.name,
    required this.batchSizeLiters,
    required this.fermentables,
    required this.yeast,
    this.style,
    this.brewer,
    this.hops = const [],
    this.waterProfile,
    this.mashSteps = const [],
    this.expectedOg,
    this.expectedFg,
    this.expectedAbv,
    this.ibu,
    this.colorSrm,
    this.brewhouseEfficiency,
    this.notes,
  });

  final String name;
  final double batchSizeLiters;
  final List<RecipeFermentable> fermentables;
  final List<Map<String, dynamic>> yeast;
  final String? style;
  final String? brewer;
  final List<RecipeHop> hops;
  final Map<String, dynamic>? waterProfile;
  final List<MashStep> mashSteps;
  final double? expectedOg;
  final double? expectedFg;
  final double? expectedAbv;
  final double? ibu;
  final double? colorSrm;
  final double? brewhouseEfficiency;
  final String? notes;

  Map<String, dynamic> toJson() => {
    'name': name,
    'style': style,
    'brewer': brewer,
    'batch_size_liters': batchSizeLiters,
    'fermentables':
        fermentables
            .map(
              (f) => {
                'name': f.name,
                'amount_kg': f.amountKg,
                if (f.sku != null) 'sku': f.sku,
                if (f.colorSrm != null) 'color_srm': f.colorSrm,
                if (f.type != null) 'type': f.type,
              },
            )
            .toList(),
    'hops':
        hops
            .map(
              (h) => {
                'name': h.name,
                'amount_g': h.amountG,
                if (h.sku != null) 'sku': h.sku,
                if (h.timeMim != null) 'time_min': h.timeMim,
                if (h.use != null) 'use': h.use,
                if (h.alphaAcid != null) 'alpha_acid': h.alphaAcid,
              },
            )
            .toList(),
    'yeast': yeast,
    if (waterProfile != null) 'water_profile': waterProfile,
    if (mashSteps.isNotEmpty)
      'mash_steps':
          mashSteps
              .map(
                (m) => {
                  'step': m.step,
                  'temp_c': m.tempC,
                  'time_min': m.timeMin,
                },
              )
              .toList(),
    if (expectedOg != null) 'expected_og': expectedOg,
    if (expectedFg != null) 'expected_fg': expectedFg,
    if (expectedAbv != null) 'expected_abv': expectedAbv,
    if (ibu != null) 'ibu': ibu,
    if (colorSrm != null) 'color_srm': colorSrm,
    if (brewhouseEfficiency != null)
      'brewhouse_efficiency': brewhouseEfficiency,
    if (notes != null && notes!.trim().isNotEmpty) 'notes': notes,
  };

  @override
  List<Object?> get props => [name, batchSizeLiters, fermentables, yeast];
}

/// Payload for partial recipe updates.
class RecipePatch extends Equatable {
  const RecipePatch({
    this.name,
    this.style,
    this.brewer,
    this.batchSizeLiters,
    this.fermentables,
    this.hops,
    this.yeast,
    this.waterProfile,
    this.mashSteps,
    this.expectedOg,
    this.expectedFg,
    this.expectedAbv,
    this.ibu,
    this.colorSrm,
    this.brewhouseEfficiency,
    this.notes,
  });

  final String? name;
  final String? style;
  final String? brewer;
  final double? batchSizeLiters;
  final List<RecipeFermentable>? fermentables;
  final List<RecipeHop>? hops;
  final List<Map<String, dynamic>>? yeast;
  final Map<String, dynamic>? waterProfile;
  final List<MashStep>? mashSteps;
  final double? expectedOg;
  final double? expectedFg;
  final double? expectedAbv;
  final double? ibu;
  final double? colorSrm;
  final double? brewhouseEfficiency;
  final String? notes;

  bool get isEmpty =>
      name == null &&
      style == null &&
      brewer == null &&
      batchSizeLiters == null &&
      fermentables == null &&
      hops == null &&
      yeast == null &&
      waterProfile == null &&
      mashSteps == null &&
      expectedOg == null &&
      expectedFg == null &&
      expectedAbv == null &&
      ibu == null &&
      colorSrm == null &&
      brewhouseEfficiency == null &&
      notes == null;

  Map<String, dynamic> toJson() {
    final payload = <String, dynamic>{};
    if (name != null) payload['name'] = name;
    if (style != null) payload['style'] = style;
    if (brewer != null) payload['brewer'] = brewer;
    if (batchSizeLiters != null) payload['batch_size_liters'] = batchSizeLiters;
    if (fermentables != null) {
      payload['fermentables'] =
          fermentables!
              .map(
                (f) => {
                  'name': f.name,
                  'amount_kg': f.amountKg,
                  if (f.sku != null) 'sku': f.sku,
                  if (f.colorSrm != null) 'color_srm': f.colorSrm,
                  if (f.type != null) 'type': f.type,
                },
              )
              .toList();
    }
    if (hops != null) {
      payload['hops'] =
          hops!
              .map(
                (h) => {
                  'name': h.name,
                  'amount_g': h.amountG,
                  if (h.sku != null) 'sku': h.sku,
                  if (h.timeMim != null) 'time_min': h.timeMim,
                  if (h.use != null) 'use': h.use,
                  if (h.alphaAcid != null) 'alpha_acid': h.alphaAcid,
                },
              )
              .toList();
    }
    if (yeast != null) payload['yeast'] = yeast;
    if (waterProfile != null) payload['water_profile'] = waterProfile;
    if (mashSteps != null) {
      payload['mash_steps'] =
          mashSteps!
              .map(
                (m) => {
                  'step': m.step,
                  'temp_c': m.tempC,
                  'time_min': m.timeMin,
                },
              )
              .toList();
    }
    if (expectedOg != null) payload['expected_og'] = expectedOg;
    if (expectedFg != null) payload['expected_fg'] = expectedFg;
    if (expectedAbv != null) payload['expected_abv'] = expectedAbv;
    if (ibu != null) payload['ibu'] = ibu;
    if (colorSrm != null) payload['color_srm'] = colorSrm;
    if (brewhouseEfficiency != null) {
      payload['brewhouse_efficiency'] = brewhouseEfficiency;
    }
    if (notes != null) payload['notes'] = notes;
    return payload;
  }

  @override
  List<Object?> get props => [
    name,
    style,
    brewer,
    batchSizeLiters,
    fermentables,
    hops,
    yeast,
    waterProfile,
    mashSteps,
    expectedOg,
    expectedFg,
    expectedAbv,
    ibu,
    colorSrm,
    brewhouseEfficiency,
    notes,
  ];
}
