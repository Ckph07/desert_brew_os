import '../../domain/entities/recipe_stock_validation.dart';

class RecipeStockValidationItemModel extends RecipeStockValidationItem {
  const RecipeStockValidationItemModel({
    required super.ingredientType,
    required super.name,
    required super.lookupKey,
    required super.requiredQuantity,
    required super.unit,
    required super.availableQuantity,
    required super.status,
    required super.matchedBatches,
    super.sku,
  });

  factory RecipeStockValidationItemModel.fromJson(Map<String, dynamic> json) {
    return RecipeStockValidationItemModel(
      ingredientType: json['ingredient_type'] as String? ?? 'UNKNOWN',
      name: json['name'] as String? ?? 'UNKNOWN',
      sku: json['sku'] as String?,
      lookupKey: json['lookup_key'] as String? ?? '',
      requiredQuantity: (json['required_quantity'] as num?)?.toDouble() ?? 0.0,
      unit: json['unit'] as String? ?? '',
      availableQuantity:
          (json['available_quantity'] as num?)?.toDouble() ?? 0.0,
      status: stockValidationStatusFromString(
        json['status'] as String? ?? 'MISSING',
      ),
      matchedBatches: (json['matched_batches'] as num?)?.toInt() ?? 0,
    );
  }
}

class RecipeStockValidationModel extends RecipeStockValidation {
  const RecipeStockValidationModel({
    required super.recipeId,
    required super.recipeName,
    required super.scaleFactor,
    required super.plannedVolumeLiters,
    required super.items,
    required super.allAvailable,
  });

  factory RecipeStockValidationModel.fromJson(Map<String, dynamic> json) {
    final rawItems = (json['items'] as List<dynamic>? ?? []);
    final items =
        rawItems
            .map(
              (row) => RecipeStockValidationItemModel.fromJson(
                row as Map<String, dynamic>,
              ),
            )
            .toList();

    return RecipeStockValidationModel(
      recipeId: (json['recipe_id'] as num?)?.toInt() ?? 0,
      recipeName: json['recipe_name'] as String? ?? '',
      scaleFactor: (json['scale_factor'] as num?)?.toDouble() ?? 1.0,
      plannedVolumeLiters:
          (json['planned_volume_liters'] as num?)?.toDouble() ?? 0.0,
      items: items,
      allAvailable: json['all_available'] as bool? ?? false,
    );
  }
}
