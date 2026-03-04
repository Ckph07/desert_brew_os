import 'package:equatable/equatable.dart';

/// Keg FSM states.
/// EMPTY → CLEANING → CLEAN → FULL → DELIVERED → IN_CLIENT → RETURNED → CLEANING
enum KegState {
  empty,
  cleaning,
  clean,
  full,
  delivered,
  inClient,
  returned,
  maintenance;

  factory KegState.fromString(String s) {
    switch (s.toUpperCase()) {
      case 'EMPTY':
        return KegState.empty;
      case 'CLEANING':
        return KegState.cleaning;
      case 'CLEAN':
        return KegState.clean;
      case 'FULL':
        return KegState.full;
      case 'DELIVERED':
        return KegState.delivered;
      case 'IN_CLIENT':
        return KegState.inClient;
      case 'RETURNED':
        return KegState.returned;
      case 'MAINTENANCE':
        return KegState.maintenance;
      default:
        return KegState.empty;
    }
  }

  String get displayName {
    switch (this) {
      case KegState.empty:
        return 'Vacío';
      case KegState.cleaning:
        return 'Limpiando';
      case KegState.clean:
        return 'Limpio';
      case KegState.full:
        return 'Lleno';
      case KegState.delivered:
        return 'Entregado';
      case KegState.inClient:
        return 'En Cliente';
      case KegState.returned:
        return 'Devuelto';
      case KegState.maintenance:
        return 'Mantenimiento';
    }
  }

  bool get isAvailable =>
      this == KegState.empty || this == KegState.clean;
  bool get isFilled =>
      this == KegState.full || this == KegState.delivered || this == KegState.inClient;
}

/// Keg domain entity (UUID-keyed physical asset).
class KegAsset extends Equatable {
  const KegAsset({
    required this.id,
    required this.serialNumber,
    required this.sizeLiters,
    required this.kegType,
    required this.currentState,
    required this.ownership,
    required this.cycleCount,
    required this.isActive,
    required this.needsMaintenance,
    required this.createdAt,
    required this.updatedAt,
    this.rfidTag,
    this.productionBatchId,
    this.clientId,
    this.currentLocation,
    this.lastCleanedAt,
    this.lastFilledAt,
    this.isAvailable = false,
    this.isFilled = false,
    this.guestBreweryId,
  });

  final String id; // UUID as string
  final String serialNumber;
  final int sizeLiters;
  final String kegType;   // SANKE_D, EURO_KOMB, CORNY_PIN, CORNY_BALL
  final KegState currentState;
  final String ownership; // OWN | GUEST
  final int cycleCount;
  final bool isActive;
  final bool needsMaintenance;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? rfidTag;
  final int? productionBatchId;
  final int? clientId;
  final String? currentLocation;
  final DateTime? lastCleanedAt;
  final DateTime? lastFilledAt;
  final bool isAvailable;
  final bool isFilled;
  final int? guestBreweryId;

  @override
  List<Object?> get props => [id, serialNumber, currentState];
}
