import 'package:equatable/equatable.dart';

class SecurityDevice extends Equatable {
  const SecurityDevice({
    required this.id,
    required this.deviceId,
    required this.deviceModel,
    required this.assignedUserName,
    required this.status,
    required this.enrolledAt,
    required this.daysSinceHeartbeat,
    this.lastHeartbeat,
  });

  final String id;
  final String deviceId;
  final String deviceModel;
  final String assignedUserName;
  final String status;
  final DateTime enrolledAt;
  final DateTime? lastHeartbeat;
  final int daysSinceHeartbeat;

  bool get isPending => status.toLowerCase() == 'pending';
  bool get isActive => status.toLowerCase() == 'active';
  bool get isRevoked => status.toLowerCase() == 'revoked';

  @override
  List<Object?> get props => [
    id,
    deviceId,
    deviceModel,
    assignedUserName,
    status,
    enrolledAt,
    lastHeartbeat,
    daysSinceHeartbeat,
  ];
}

class SecurityEnrollmentStats extends Equatable {
  const SecurityEnrollmentStats({
    required this.byStatus,
    required this.total,
    required this.staleDevices7d,
  });

  final Map<String, int> byStatus;
  final int total;
  final int staleDevices7d;

  int get active => byStatus['active'] ?? 0;
  int get pending => byStatus['pending'] ?? 0;
  int get revoked => byStatus['revoked'] ?? 0;

  @override
  List<Object?> get props => [byStatus, total, staleDevices7d];
}
