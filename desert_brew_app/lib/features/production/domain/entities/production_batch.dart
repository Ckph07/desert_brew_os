import 'package:equatable/equatable.dart';

/// Production batch FSM states.
/// PLANNED → BREWING → FERMENTING → CONDITIONING → PACKAGING → COMPLETED
enum BatchStatus {
  planned,
  brewing,
  fermenting,
  conditioning,
  packaging,
  completed,
  cancelled;

  factory BatchStatus.fromString(String s) {
    return BatchStatus.values.firstWhere(
      (e) => e.name.toUpperCase() == s.toUpperCase(),
      orElse: () => BatchStatus.planned,
    );
  }

  String get displayName {
    switch (this) {
      case BatchStatus.planned:
        return 'Planificado';
      case BatchStatus.brewing:
        return 'Macerado';
      case BatchStatus.fermenting:
        return 'Fermentando';
      case BatchStatus.conditioning:
        return 'Acondicionando';
      case BatchStatus.packaging:
        return 'Envasando';
      case BatchStatus.completed:
        return 'Completado';
      case BatchStatus.cancelled:
        return 'Cancelado';
    }
  }

  bool get isActive =>
      this == BatchStatus.brewing ||
      this == BatchStatus.fermenting ||
      this == BatchStatus.conditioning ||
      this == BatchStatus.packaging;
}

/// FIFO cost breakdown for a production batch.
class BatchCostBreakdown extends Equatable {
  const BatchCostBreakdown({
    required this.malt,
    required this.hops,
    required this.yeast,
    required this.water,
    required this.labor,
    required this.overhead,
  });

  final double malt;
  final double hops;
  final double yeast;
  final double water;
  final double labor;
  final double overhead;

  double get total => malt + hops + yeast + water + labor + overhead;

  @override
  List<Object?> get props => [malt, hops, yeast, water, labor, overhead];
}

/// Production batch domain entity.
class ProductionBatch extends Equatable {
  const ProductionBatch({
    required this.id,
    required this.batchNumber,
    required this.recipeId,
    required this.recipeName,
    required this.status,
    required this.plannedVolumeLiters,
    required this.plannedAt,
    this.actualVolumeLiters,
    this.totalCost,
    this.costPerLiter,
    this.maltCost,
    this.hopsCost,
    this.yeastCost,
    this.waterCost,
    this.laborCost,
    this.overheadCost,
    this.actualOg,
    this.actualFg,
    this.actualAbv,
    this.yieldPercentage,
    this.daysInProduction,
    this.brewingStartedAt,
    this.fermentingStartedAt,
    this.conditioningStartedAt,
    this.packagingStartedAt,
    this.completedAt,
    this.notes,
  });

  final int id;
  final String batchNumber;
  final int recipeId;
  final String recipeName;
  final BatchStatus status;
  final double plannedVolumeLiters;
  final DateTime plannedAt;
  final double? actualVolumeLiters;
  final double? totalCost;
  final double? costPerLiter;
  // FIFO cost breakdown
  final double? maltCost;
  final double? hopsCost;
  final double? yeastCost;
  final double? waterCost;
  final double? laborCost;
  final double? overheadCost;
  // Measurements
  final double? actualOg;
  final double? actualFg;
  final double? actualAbv;
  final double? yieldPercentage;
  final int? daysInProduction;
  // Timestamps
  final DateTime? brewingStartedAt;
  final DateTime? fermentingStartedAt;
  final DateTime? conditioningStartedAt;
  final DateTime? packagingStartedAt;
  final DateTime? completedAt;
  final String? notes;

  bool get isActive => status.isActive;
  bool get isCompleted => status == BatchStatus.completed;
  bool get isPlanned => status == BatchStatus.planned;

  BatchCostBreakdown? get costBreakdown {
    if (maltCost == null) return null;
    return BatchCostBreakdown(
      malt: maltCost ?? 0,
      hops: hopsCost ?? 0,
      yeast: yeastCost ?? 0,
      water: waterCost ?? 0,
      labor: laborCost ?? 0,
      overhead: overheadCost ?? 0,
    );
  }

  @override
  List<Object?> get props => [id, batchNumber, status];
}
