import '../entities/security_device.dart';

abstract class SecurityRepository {
  Future<List<SecurityDevice>> getDevices({
    String? status,
    int? userId,
    int skip,
    int limit,
  });

  Future<SecurityEnrollmentStats> getEnrollmentStats();

  Future<SecurityDevice> enrollDevice(Map<String, dynamic> payload);

  Future<void> approveDevice({
    required String deviceId,
    required int adminUserId,
  });

  Future<void> revokeDevice({
    required String deviceId,
    required String reason,
    required int adminUserId,
  });

  Future<void> heartbeat({required String deviceId});
}
