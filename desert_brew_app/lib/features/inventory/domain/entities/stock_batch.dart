import 'package:equatable/equatable.dart';

/// Stock batch domain entity — a lot of raw material received from a supplier.
///
/// Corresponds to the backend `StockBatch` model with FIFO-costed inventory.
class StockBatch extends Equatable {
  const StockBatch({
    required this.id,
    required this.ingredientName,
    required this.category,
    required this.quantity,
    required this.unit,
    required this.unitCost,
    required this.totalCost,
    required this.remainingQuantity,
    this.supplierId,
    this.supplierName,
    this.batchNumber,
    this.expiryDate,
    this.receivedAt,
    this.notes,
  });

  final int id;
  final String ingredientName;
  final String category; // IngredientCategory enum value
  final double quantity;
  final String unit; // UnitMeasure enum value
  final double unitCost;
  final double totalCost;
  final double remainingQuantity;
  final int? supplierId;
  final String? supplierName;
  final String? batchNumber;
  final DateTime? expiryDate;
  final DateTime? receivedAt;
  final String? notes;

  double get usedQuantity => quantity - remainingQuantity;
  double get remainingPercent =>
      quantity > 0 ? (remainingQuantity / quantity) * 100 : 0;
  bool get isLow => remainingPercent < 20;
  bool get isEmpty => remainingQuantity <= 0;

  @override
  List<Object?> get props => [
        id, ingredientName, category, quantity, unit,
        unitCost, totalCost, remainingQuantity, supplierId,
      ];
}
