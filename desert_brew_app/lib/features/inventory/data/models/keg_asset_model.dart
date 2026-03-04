import '../../domain/entities/keg_asset.dart';

class KegAssetModel extends KegAsset {
  const KegAssetModel({
    required super.id,
    required super.serialNumber,
    required super.sizeLiters,
    required super.kegType,
    required super.currentState,
    required super.ownership,
    required super.cycleCount,
    required super.isActive,
    required super.needsMaintenance,
    required super.createdAt,
    required super.updatedAt,
    super.rfidTag,
    super.productionBatchId,
    super.clientId,
    super.currentLocation,
    super.lastCleanedAt,
    super.lastFilledAt,
    super.isAvailable,
    super.isFilled,
    super.guestBreweryId,
  });

  factory KegAssetModel.fromJson(Map<String, dynamic> j) {
    DateTime? _dt(String? k) => k != null ? DateTime.tryParse(k) : null;
    return KegAssetModel(
      id: j['id'] as String,
      serialNumber: j['serial_number'] as String,
      sizeLiters: (j['size_liters'] as num).toInt(),
      kegType: j['keg_type'] as String,
      currentState: KegState.fromString(j['current_state'] as String),
      ownership: j['ownership'] as String,
      cycleCount: (j['cycle_count'] as num).toInt(),
      isActive: j['is_active'] as bool? ?? true,
      needsMaintenance: j['needs_maintenance'] as bool? ?? false,
      createdAt: DateTime.parse(j['created_at'] as String),
      updatedAt: DateTime.parse(j['updated_at'] as String),
      rfidTag: j['rfid_tag'] as String?,
      productionBatchId: (j['production_batch_id'] as num?)?.toInt(),
      clientId: (j['client_id'] as num?)?.toInt(),
      currentLocation: j['current_location'] as String?,
      lastCleanedAt: _dt(j['last_cleaned_at'] as String?),
      lastFilledAt: _dt(j['last_filled_at'] as String?),
      isAvailable: j['is_available'] as bool? ?? false,
      isFilled: j['is_filled'] as bool? ?? false,
      guestBreweryId: (j['guest_brewery_id'] as num?)?.toInt(),
    );
  }
}
