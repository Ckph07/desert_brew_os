import '../../domain/entities/finished_product.dart';

class FinishedProductModel extends FinishedProduct {
  const FinishedProductModel({
    required super.id,
    required super.sku,
    required super.productName,
    required super.productType,
    required super.category,
    required super.quantity,
    required super.unitMeasure,
    required super.coldRoomId,
    required super.availabilityStatus,
    required super.receivedDate,
    required super.isAvailable,
    required super.value,
    super.productionBatchId,
    super.supplierId,
    super.guestBreweryId,
    super.kegAssetId,
    super.shelfPosition,
    super.unitCost,
    super.totalCost,
    super.productionDate,
    super.bestBefore,
    super.notes,
  });

  factory FinishedProductModel.fromJson(Map<String, dynamic> j) {
    DateTime? _dt(String? k) => k != null ? DateTime.tryParse(k) : null;
    return FinishedProductModel(
      id: (j['id'] as num).toInt(),
      sku: j['sku'] as String,
      productName: j['product_name'] as String,
      productType: ProductType.fromString(j['product_type'] as String),
      category: j['category'] as String,
      quantity: (j['quantity'] as num).toDouble(),
      unitMeasure: j['unit_measure'] as String,
      coldRoomId: j['cold_room_id'] as String,
      availabilityStatus:
          AvailabilityStatus.fromString(j['availability_status'] as String),
      receivedDate: DateTime.parse(j['received_date'] as String),
      isAvailable: j['is_available'] as bool? ?? false,
      value: (j['value'] as num).toDouble(),
      productionBatchId: (j['production_batch_id'] as num?)?.toInt(),
      supplierId: (j['supplier_id'] as num?)?.toInt(),
      guestBreweryId: (j['guest_brewery_id'] as num?)?.toInt(),
      kegAssetId: j['keg_asset_id'] as String?,
      shelfPosition: j['shelf_position'] as String?,
      unitCost: (j['unit_cost'] as num?)?.toDouble(),
      totalCost: (j['total_cost'] as num?)?.toDouble(),
      productionDate: _dt(j['production_date'] as String?),
      bestBefore: _dt(j['best_before'] as String?),
      notes: j['notes'] as String?,
    );
  }
}

class ColdRoomStatusModel extends ColdRoomStatus {
  const ColdRoomStatusModel({
    required super.id,
    required super.currentTemp,
    required super.targetTemp,
    required super.lastReading,
    required super.alertActive,
    super.utilizationPercent,
  });

  factory ColdRoomStatusModel.fromJson(Map<String, dynamic> j) =>
      ColdRoomStatusModel(
        id: j['id'] as String,
        currentTemp: (j['current_temp'] as num).toDouble(),
        targetTemp: (j['target_temp'] as num?)?.toDouble() ?? 4.0,
        lastReading: DateTime.parse(j['last_reading'] as String),
        alertActive: j['alert_active'] as bool? ?? false,
        utilizationPercent:
            (j['utilization_percent'] as num?)?.toDouble(),
      );
}
