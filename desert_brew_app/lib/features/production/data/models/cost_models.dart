import '../../domain/entities/cost_entities.dart';

class IngredientPriceModel extends IngredientPrice {
  const IngredientPriceModel({
    required super.id,
    required super.name,
    required super.category,
    required super.unitMeasure,
    required super.currentPrice,
    required super.currency,
    required super.isActive,
    super.supplierName,
    super.supplierSku,
    super.notes,
    super.lastPriceUpdate,
  });

  factory IngredientPriceModel.fromJson(Map<String, dynamic> j) =>
      IngredientPriceModel(
        id: j['id'] as int,
        name: j['name'] as String,
        category: j['category'] as String,
        unitMeasure: j['unit_measure'] as String,
        currentPrice: (j['current_price'] as num).toDouble(),
        currency: j['currency'] as String? ?? 'MXN',
        isActive: j['is_active'] as bool? ?? true,
        supplierName: j['supplier_name'] as String?,
        supplierSku: j['supplier_sku'] as String?,
        notes: j['notes'] as String?,
        lastPriceUpdate: j['last_price_update'] != null
            ? DateTime.tryParse(j['last_price_update'] as String)
            : null,
      );
}

class FixedMonthlyCostModel extends FixedMonthlyCost {
  const FixedMonthlyCostModel({
    required super.id,
    required super.category,
    required super.concept,
    required super.monthlyAmount,
    required super.isActive,
    super.notes,
  });

  factory FixedMonthlyCostModel.fromJson(Map<String, dynamic> j) =>
      FixedMonthlyCostModel(
        id: j['id'] as int,
        category: j['category'] as String,
        concept: j['concept'] as String,
        monthlyAmount: (j['monthly_amount'] as num).toDouble(),
        isActive: j['is_active'] as bool? ?? true,
        notes: j['notes'] as String?,
      );
}

class CostSummaryModel extends CostSummary {
  const CostSummaryModel({
    required super.totalFixedMonthly,
    required super.targetLiters,
    required super.fixedCostPerLiter,
    required super.costBreakdown,
    required super.ingredientCount,
    super.ingredientTotalEstimated,
  });

  factory CostSummaryModel.fromJson(Map<String, dynamic> j) => CostSummaryModel(
        totalFixedMonthly: (j['total_fixed_monthly'] as num).toDouble(),
        targetLiters: (j['target_liters'] as num).toDouble(),
        fixedCostPerLiter: (j['fixed_cost_per_liter'] as num).toDouble(),
        costBreakdown: (j['cost_breakdown'] as List<dynamic>? ?? [])
            .map((e) => e as Map<String, dynamic>)
            .toList(),
        ingredientCount: (j['ingredient_count'] as num).toInt(),
        ingredientTotalEstimated:
            (j['ingredient_total_estimated'] as num?)?.toDouble(),
      );
}
