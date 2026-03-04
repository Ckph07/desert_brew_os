import 'package:equatable/equatable.dart';

/// Ingredient price entry — used for cost estimates.
class IngredientPrice extends Equatable {
  const IngredientPrice({
    required this.id,
    required this.name,
    required this.category,
    required this.unitMeasure,
    required this.currentPrice,
    required this.currency,
    required this.isActive,
    this.supplierName,
    this.supplierSku,
    this.notes,
    this.lastPriceUpdate,
  });

  final int id;
  final String name;
  final String category; // MALT | HOP | YEAST | ADJUNCT | CHEMICAL | PACKAGING | OTHER
  final String unitMeasure;
  final double currentPrice;
  final String currency;
  final bool isActive;
  final String? supplierName;
  final String? supplierSku;
  final String? notes;
  final DateTime? lastPriceUpdate;

  @override
  List<Object?> get props => [id, name, category, currentPrice];
}

/// Fixed monthly cost entry (overhead, utilities, labor…).
class FixedMonthlyCost extends Equatable {
  const FixedMonthlyCost({
    required this.id,
    required this.category,
    required this.concept,
    required this.monthlyAmount,
    required this.isActive,
    this.notes,
  });

  final int id;
  final String category; // FUEL | ENERGY | WATER | HR | OPERATIONS | GAS_CO2 ...
  final String concept;
  final double monthlyAmount;
  final bool isActive;
  final String? notes;

  @override
  List<Object?> get props => [id, concept, monthlyAmount];
}

/// Consolidated cost summary response.
class CostSummary extends Equatable {
  const CostSummary({
    required this.totalFixedMonthly,
    required this.targetLiters,
    required this.fixedCostPerLiter,
    required this.costBreakdown,
    required this.ingredientCount,
    this.ingredientTotalEstimated,
  });

  final double totalFixedMonthly;
  final double targetLiters;
  final double fixedCostPerLiter;
  final List<Map<String, dynamic>> costBreakdown;
  final int ingredientCount;
  final double? ingredientTotalEstimated;

  @override
  List<Object?> get props =>
      [totalFixedMonthly, targetLiters, fixedCostPerLiter];
}
