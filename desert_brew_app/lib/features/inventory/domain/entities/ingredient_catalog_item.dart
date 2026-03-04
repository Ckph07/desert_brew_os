import 'package:equatable/equatable.dart';

/// Catalog item used to select insumos while receiving stock.
class IngredientCatalogItem extends Equatable {
  const IngredientCatalogItem({
    required this.id,
    required this.sku,
    required this.name,
    required this.category,
    required this.unitMeasure,
    this.notes,
    this.isActive = true,
    this.createdAt,
    this.updatedAt,
  });

  final int id;
  final String sku;
  final String name;
  final String category;
  final String unitMeasure;
  final String? notes;
  final bool isActive;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  @override
  List<Object?> get props => [
    id,
    sku,
    name,
    category,
    unitMeasure,
    notes,
    isActive,
  ];
}
