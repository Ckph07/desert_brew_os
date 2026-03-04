import 'package:equatable/equatable.dart';

enum StockValidationStatus { ok, missing, insufficient }

StockValidationStatus stockValidationStatusFromString(String value) {
  switch (value.toUpperCase()) {
    case 'OK':
      return StockValidationStatus.ok;
    case 'MISSING':
      return StockValidationStatus.missing;
    case 'INSUFFICIENT':
      return StockValidationStatus.insufficient;
    default:
      return StockValidationStatus.missing;
  }
}

class RecipeStockValidationItem extends Equatable {
  const RecipeStockValidationItem({
    required this.ingredientType,
    required this.name,
    required this.lookupKey,
    required this.requiredQuantity,
    required this.unit,
    required this.availableQuantity,
    required this.status,
    required this.matchedBatches,
    this.sku,
  });

  final String ingredientType;
  final String name;
  final String? sku;
  final String lookupKey;
  final double requiredQuantity;
  final String unit;
  final double availableQuantity;
  final StockValidationStatus status;
  final int matchedBatches;

  @override
  List<Object?> get props => [
    ingredientType,
    name,
    sku,
    lookupKey,
    requiredQuantity,
    unit,
    availableQuantity,
    status,
    matchedBatches,
  ];
}

class RecipeStockValidation extends Equatable {
  const RecipeStockValidation({
    required this.recipeId,
    required this.recipeName,
    required this.scaleFactor,
    required this.plannedVolumeLiters,
    required this.items,
    required this.allAvailable,
  });

  final int recipeId;
  final String recipeName;
  final double scaleFactor;
  final double plannedVolumeLiters;
  final List<RecipeStockValidationItem> items;
  final bool allAvailable;

  @override
  List<Object?> get props => [
    recipeId,
    recipeName,
    scaleFactor,
    plannedVolumeLiters,
    items,
    allAvailable,
  ];
}
