import '../../domain/entities/security_device.dart';

class SecurityDeviceModel extends SecurityDevice {
  const SecurityDeviceModel({
    required super.id,
    required super.deviceId,
    required super.deviceModel,
    required super.assignedUserName,
    required super.status,
    required super.enrolledAt,
    required super.daysSinceHeartbeat,
    super.lastHeartbeat,
  });

  factory SecurityDeviceModel.fromJson(Map<String, dynamic> json) {
    return SecurityDeviceModel(
      id: json['id'] as String,
      deviceId: json['device_id'] as String,
      deviceModel: json['device_model'] as String? ?? '-',
      assignedUserName: json['assigned_user_name'] as String? ?? '-',
      status: (json['status'] as String? ?? '').toLowerCase(),
      enrolledAt: DateTime.parse(json['enrolled_at'] as String),
      lastHeartbeat:
          json['last_heartbeat'] != null
              ? DateTime.parse(json['last_heartbeat'] as String)
              : null,
      daysSinceHeartbeat: (json['days_since_heartbeat'] as num?)?.toInt() ?? 0,
    );
  }
}

class SecurityEnrollmentStatsModel extends SecurityEnrollmentStats {
  const SecurityEnrollmentStatsModel({
    required super.byStatus,
    required super.total,
    required super.staleDevices7d,
  });

  factory SecurityEnrollmentStatsModel.fromJson(Map<String, dynamic> json) {
    final rawStatus = (json['by_status'] as Map<String, dynamic>? ?? const {});
    final byStatus = rawStatus.map(
      (key, value) => MapEntry(key.toLowerCase(), (value as num).toInt()),
    );

    return SecurityEnrollmentStatsModel(
      byStatus: byStatus,
      total: (json['total'] as num?)?.toInt() ?? 0,
      staleDevices7d: (json['stale_devices_7d'] as num?)?.toInt() ?? 0,
    );
  }
}
