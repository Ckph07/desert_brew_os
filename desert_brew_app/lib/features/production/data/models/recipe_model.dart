import '../../domain/entities/recipe.dart';

class RecipeModel extends Recipe {
  const RecipeModel({
    required super.id,
    required super.name,
    required super.batchSizeLiters,
    required super.fermentables,
    required super.hops,
    required super.importedAt,
    super.style,
    super.brewer,
    super.yeast,
    super.mashSteps,
    super.waterProfile,
    super.expectedOg,
    super.expectedFg,
    super.expectedAbv,
    super.ibu,
    super.colorSrm,
    super.brewhouseEfficiency,
    super.notes,
  });

  factory RecipeModel.fromJson(Map<String, dynamic> j) {
    final fermentables =
        (j['fermentables'] as List<dynamic>? ?? [])
            .map((e) => RecipeFermentable.fromJson(e as Map<String, dynamic>))
            .toList();
    final hops =
        (j['hops'] as List<dynamic>? ?? [])
            .map((e) => RecipeHop.fromJson(e as Map<String, dynamic>))
            .toList();
    final mashSteps =
        (j['mash_steps'] as List<dynamic>? ?? [])
            .map((e) => MashStep.fromJson(e as Map<String, dynamic>))
            .toList();
    final yeast =
        (j['yeast'] as List<dynamic>? ?? [])
            .map((e) => e as Map<String, dynamic>)
            .toList();

    return RecipeModel(
      id: j['id'] as int,
      name: j['name'] as String,
      batchSizeLiters: (j['batch_size_liters'] as num).toDouble(),
      fermentables: fermentables,
      hops: hops,
      yeast: yeast,
      mashSteps: mashSteps,
      waterProfile: j['water_profile'] as Map<String, dynamic>?,
      importedAt: DateTime.parse(j['imported_at'] as String),
      style: j['style'] as String?,
      brewer: j['brewer'] as String?,
      expectedOg: (j['expected_og'] as num?)?.toDouble(),
      expectedFg: (j['expected_fg'] as num?)?.toDouble(),
      expectedAbv: (j['expected_abv'] as num?)?.toDouble(),
      ibu: (j['ibu'] as num?)?.toDouble(),
      colorSrm: (j['color_srm'] as num?)?.toDouble(),
      brewhouseEfficiency: (j['brewhouse_efficiency'] as num?)?.toDouble(),
      notes: j['notes'] as String?,
    );
  }
}
