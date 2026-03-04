import '../../domain/entities/security_device.dart';
import '../../domain/repositories/security_repository.dart';
import '../datasources/security_remote_datasource.dart';

class SecurityRepositoryImpl implements SecurityRepository {
  SecurityRepositoryImpl(this._remote);

  final SecurityRemoteDataSource _remote;

  @override
  Future<List<SecurityDevice>> getDevices({
    String? status,
    int? userId,
    int skip = 0,
    int limit = 100,
  }) => _remote.getDevices(
    status: status,
    userId: userId,
    skip: skip,
    limit: limit,
  );

  @override
  Future<SecurityEnrollmentStats> getEnrollmentStats() =>
      _remote.getEnrollmentStats();

  @override
  Future<SecurityDevice> enrollDevice(Map<String, dynamic> payload) =>
      _remote.enrollDevice(payload);

  @override
  Future<void> approveDevice({
    required String deviceId,
    required int adminUserId,
  }) => _remote.approveDevice(deviceId: deviceId, adminUserId: adminUserId);

  @override
  Future<void> revokeDevice({
    required String deviceId,
    required String reason,
    required int adminUserId,
  }) => _remote.revokeDevice(
    deviceId: deviceId,
    reason: reason,
    adminUserId: adminUserId,
  );

  @override
  Future<void> heartbeat({required String deviceId}) =>
      _remote.heartbeat(deviceId: deviceId);
}
