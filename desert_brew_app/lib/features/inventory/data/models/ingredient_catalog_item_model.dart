import '../../domain/entities/ingredient_catalog_item.dart';

/// Data model for ingredient catalog API responses.
class IngredientCatalogItemModel extends IngredientCatalogItem {
  const IngredientCatalogItemModel({
    required super.id,
    required super.sku,
    required super.name,
    required super.category,
    required super.unitMeasure,
    super.notes,
    super.isActive,
    super.createdAt,
    super.updatedAt,
  });

  factory IngredientCatalogItemModel.fromJson(Map<String, dynamic> json) {
    return IngredientCatalogItemModel(
      id: json['id'] as int,
      sku: json['sku'] as String,
      name: json['name'] as String,
      category: json['category'] as String,
      unitMeasure:
          (json['unit_measure'] as String?) ??
          (json['default_unit'] as String?) ??
          'UNIT',
      notes: json['notes'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      createdAt:
          json['created_at'] != null
              ? DateTime.parse(json['created_at'] as String)
              : null,
      updatedAt:
          json['updated_at'] != null
              ? DateTime.parse(json['updated_at'] as String)
              : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'sku': sku,
    'category': category,
    'unit_measure': unitMeasure,
    if (notes != null && notes!.trim().isNotEmpty) 'notes': notes,
  };
}
