part of 'stock_bloc.dart';

abstract class StockEvent {}

/// Load the stock batch list with optional filters.
class StockLoadRequested extends StockEvent {
  StockLoadRequested({this.category, this.search, this.lowStockOnly});
  final String? category;
  final String? search;
  final bool? lowStockOnly;
}

/// Reload after receiving new stock.
class StockRefreshRequested extends StockEvent {}

/// Submit a new stock receipt form.
class StockReceiveSubmitted extends StockEvent {
  StockReceiveSubmitted({
    required this.ingredientName,
    required this.category,
    required this.quantity,
    required this.unit,
    required this.unitCost,
    this.supplierId,
    this.batchNumber,
    this.expiryDate,
    this.notes,
  });
  final String ingredientName;
  final String category;
  final double quantity;
  final String unit;
  final double unitCost;
  final int? supplierId;
  final String? batchNumber;
  final DateTime? expiryDate;
  final String? notes;
}
