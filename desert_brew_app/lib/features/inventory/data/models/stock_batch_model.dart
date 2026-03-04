import '../../domain/entities/stock_batch.dart';

/// Data model for StockBatch — handles JSON serialization.
/// Maps from backend `StockBatchResponse` schema.
class StockBatchModel extends StockBatch {
  const StockBatchModel({
    required super.id,
    required super.ingredientName,
    required super.category,
    required super.quantity,
    required super.unit,
    required super.unitCost,
    required super.totalCost,
    required super.remainingQuantity,
    super.supplierId,
    super.supplierName,
    super.batchNumber,
    super.expiryDate,
    super.receivedAt,
    super.notes,
  });

  factory StockBatchModel.fromJson(Map<String, dynamic> json) {
    return StockBatchModel(
      id: json['id'] as int,
      ingredientName:
          (json['sku'] as String?) ??
          (json['ingredient_name'] as String?) ??
          'UNKNOWN',
      category: json['category'] as String,
      quantity:
          ((json['initial_quantity'] ?? json['quantity']) as num).toDouble(),
      unit: (json['unit_measure'] as String?) ?? (json['unit'] as String),
      unitCost: (json['unit_cost'] as num).toDouble(),
      totalCost: (json['total_cost'] as num).toDouble(),
      remainingQuantity: (json['remaining_quantity'] as num).toDouble(),
      supplierId: json['supplier_id'] as int?,
      supplierName:
          (json['provider_name'] as String?) ??
          (json['supplier_name'] as String?),
      batchNumber: json['batch_number'] as String?,
      expiryDate:
          json['expiration_date'] != null
              ? DateTime.parse(json['expiration_date'] as String)
              : json['expiry_date'] != null
              ? DateTime.parse(json['expiry_date'] as String)
              : null,
      receivedAt:
          json['arrival_date'] != null
              ? DateTime.parse(json['arrival_date'] as String)
              : json['received_at'] != null
              ? DateTime.parse(json['received_at'] as String)
              : null,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'sku': ingredientName,
    'category': category,
    'quantity': quantity,
    'unit_measure': unit,
    'unit_cost': unitCost,
    if (supplierName != null) 'provider_name': supplierName,
    if (batchNumber != null) 'batch_number': batchNumber,
    if (expiryDate != null) 'expiration_date': expiryDate!.toIso8601String(),
    if (notes != null) 'notes': notes,
  };
}
