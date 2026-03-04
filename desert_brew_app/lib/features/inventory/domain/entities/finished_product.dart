import 'package:equatable/equatable.dart';

/// Available cold room location codes.
enum ColdRoomLocation {
  coldRoom1,
  coldRoom2,
  taproom,
  warehouse,
  external;

  factory ColdRoomLocation.fromString(String s) {
    switch (s.toUpperCase()) {
      case 'COLD_ROOM_1':
        return ColdRoomLocation.coldRoom1;
      case 'COLD_ROOM_2':
        return ColdRoomLocation.coldRoom2;
      case 'TAPROOM':
        return ColdRoomLocation.taproom;
      case 'WAREHOUSE':
        return ColdRoomLocation.warehouse;
      case 'EXTERNAL':
        return ColdRoomLocation.external;
      default:
        return ColdRoomLocation.coldRoom1;
    }
  }

  String get displayName {
    switch (this) {
      case ColdRoomLocation.coldRoom1:
        return 'Cámara Fría 1';
      case ColdRoomLocation.coldRoom2:
        return 'Cámara Fría 2';
      case ColdRoomLocation.taproom:
        return 'Taproom';
      case ColdRoomLocation.warehouse:
        return 'Almacén';
      case ColdRoomLocation.external:
        return 'Externo';
    }
  }
}

/// Product type: OWN_PRODUCTION | COMMERCIAL | GUEST_CRAFT | MERCHANDISE.
enum ProductType {
  ownProduction,
  commercial,
  guestCraft,
  merchandise;

  factory ProductType.fromString(String s) {
    switch (s.toUpperCase()) {
      case 'OWN_PRODUCTION':
        return ProductType.ownProduction;
      case 'COMMERCIAL':
        return ProductType.commercial;
      case 'GUEST_CRAFT':
        return ProductType.guestCraft;
      case 'MERCHANDISE':
        return ProductType.merchandise;
      default:
        return ProductType.ownProduction;
    }
  }

  String get displayName {
    switch (this) {
      case ProductType.ownProduction:
        return 'Producción Propia';
      case ProductType.commercial:
        return 'Comercial';
      case ProductType.guestCraft:
        return 'Guest Craft';
      case ProductType.merchandise:
        return 'Merchandising';
    }
  }
}

/// Availability status for a finished product.
enum AvailabilityStatus {
  available,
  reserved,
  sold,
  expired,
  damaged;

  factory AvailabilityStatus.fromString(String s) {
    switch (s.toUpperCase()) {
      case 'AVAILABLE':
        return AvailabilityStatus.available;
      case 'RESERVED':
        return AvailabilityStatus.reserved;
      case 'SOLD':
        return AvailabilityStatus.sold;
      case 'EXPIRED':
        return AvailabilityStatus.expired;
      case 'DAMAGED':
        return AvailabilityStatus.damaged;
      default:
        return AvailabilityStatus.available;
    }
  }

  String get displayName {
    switch (this) {
      case AvailabilityStatus.available:
        return 'Disponible';
      case AvailabilityStatus.reserved:
        return 'Reservado';
      case AvailabilityStatus.sold:
        return 'Vendido';
      case AvailabilityStatus.expired:
        return 'Vencido';
      case AvailabilityStatus.damaged:
        return 'Dañado';
    }
  }
}

/// Finished product inventory item (beer kegs, bottles, cans, merch).
class FinishedProduct extends Equatable {
  const FinishedProduct({
    required this.id,
    required this.sku,
    required this.productName,
    required this.productType,
    required this.category,
    required this.quantity,
    required this.unitMeasure,
    required this.coldRoomId,
    required this.availabilityStatus,
    required this.receivedDate,
    required this.isAvailable,
    required this.value,
    this.productionBatchId,
    this.supplierId,
    this.guestBreweryId,
    this.kegAssetId,
    this.shelfPosition,
    this.unitCost,
    this.totalCost,
    this.productionDate,
    this.bestBefore,
    this.notes,
  });

  final int id;
  final String sku;
  final String productName;
  final ProductType productType;
  final String category;  // BEER_KEG, BEER_BOTTLE, BEER_CAN, etc.
  final double quantity;
  final String unitMeasure;
  final String coldRoomId;
  final AvailabilityStatus availabilityStatus;
  final DateTime receivedDate;
  final bool isAvailable;
  final double value;
  final int? productionBatchId;
  final int? supplierId;
  final int? guestBreweryId;
  final String? kegAssetId;
  final String? shelfPosition;
  final double? unitCost;
  final double? totalCost;
  final DateTime? productionDate;
  final DateTime? bestBefore;
  final String? notes;

  bool get isExpiringSoon {
    if (bestBefore == null) return false;
    return bestBefore!.difference(DateTime.now()).inDays <= 7;
  }

  @override
  List<Object?> get props => [id, sku, quantity, availabilityStatus];
}

/// Cold room temperature status summary.
class ColdRoomStatus extends Equatable {
  const ColdRoomStatus({
    required this.id,
    required this.currentTemp,
    required this.targetTemp,
    required this.lastReading,
    required this.alertActive,
    this.utilizationPercent,
  });

  final String id;
  final double currentTemp;
  final double targetTemp;
  final DateTime lastReading;
  final bool alertActive;
  final double? utilizationPercent;

  bool get isWithinRange =>
      currentTemp >= 0 && currentTemp <= 7;

  @override
  List<Object?> get props => [id, currentTemp, alertActive];
}
