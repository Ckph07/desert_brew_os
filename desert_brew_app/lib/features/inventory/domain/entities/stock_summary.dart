import 'package:equatable/equatable.dart';

/// Aggregated stock summary from the backend summary endpoint.
class StockSummary extends Equatable {
  const StockSummary({
    required this.totalBatches,
    required this.totalValue,
    required this.lowStockItems,
    required this.byCategory,
  });

  final int totalBatches;
  final double totalValue;
  final int lowStockItems;
  final Map<String, double> byCategory; // category -> total_value

  @override
  List<Object?> get props => [totalBatches, totalValue, lowStockItems];
}
