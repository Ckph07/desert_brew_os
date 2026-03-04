import 'package:equatable/equatable.dart';

/// Base failure class for domain-layer error handling.
///
/// All failures are [Equatable] for BLoC state comparison.
abstract class Failure extends Equatable {
  const Failure({required this.message, this.code});

  final String message;
  final String? code;

  @override
  List<Object?> get props => [message, code];
}

/// Failure from a network/API call.
class ServerFailure extends Failure {
  const ServerFailure({
    required super.message,
    super.code,
    this.statusCode,
  });

  final int? statusCode;

  @override
  List<Object?> get props => [message, code, statusCode];
}

/// Failure from local database operations.
class CacheFailure extends Failure {
  const CacheFailure({required super.message, super.code});
}

/// Failure when device is offline and operation requires network.
class NetworkFailure extends Failure {
  const NetworkFailure({
    super.message = 'Sin conexión a la red. Verifica tu WiFi.',
  });
}

/// Failure from validation errors (form input, business rules).
class ValidationFailure extends Failure {
  const ValidationFailure({required super.message, this.field});

  final String? field;

  @override
  List<Object?> get props => [message, field];
}

/// Failure from crypto operations (Ed25519 signing/verification).
class CryptoFailure extends Failure {
  const CryptoFailure({required super.message});
}

/// Failure when a resource is not found.
class NotFoundFailure extends Failure {
  const NotFoundFailure({
    super.message = 'Recurso no encontrado.',
    this.resourceType,
    this.resourceId,
  });

  final String? resourceType;
  final String? resourceId;

  @override
  List<Object?> get props => [message, resourceType, resourceId];
}

/// Failure from insufficient stock (FIFO allocation).
class InsufficientStockFailure extends Failure {
  const InsufficientStockFailure({
    required super.message,
    this.sku,
    this.requested,
    this.available,
  });

  final String? sku;
  final double? requested;
  final double? available;
}

/// Failure from invalid state transition (batch FSM, keg FSM).
class InvalidTransitionFailure extends Failure {
  const InvalidTransitionFailure({
    required super.message,
    this.currentState,
    this.targetState,
  });

  final String? currentState;
  final String? targetState;
}
