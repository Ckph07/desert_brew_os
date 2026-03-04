import 'package:dio/dio.dart';

import '../../../../core/config/api_config.dart';
import '../../../../core/network/api_client.dart';
import '../models/security_device_model.dart';

class SecurityRemoteDataSource {
  SecurityRemoteDataSource()
    : _dio = ApiClient.forService(ServicePort.security);

  final Dio _dio;

  Future<List<SecurityDeviceModel>> getDevices({
    String? status,
    int? userId,
    int skip = 0,
    int limit = 100,
  }) async {
    final response = await _dio.get(
      '/api/v1/security/enrollments',
      queryParameters: {
        if (status != null) 'status': status,
        if (userId != null) 'user_id': userId,
        'skip': skip,
        'limit': limit,
      },
    );

    return (response.data as List<dynamic>)
        .map((e) => SecurityDeviceModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SecurityEnrollmentStatsModel> getEnrollmentStats() async {
    final response = await _dio.get('/api/v1/security/enrollments/stats');
    return SecurityEnrollmentStatsModel.fromJson(
      response.data as Map<String, dynamic>,
    );
  }

  Future<SecurityDeviceModel> enrollDevice(Map<String, dynamic> payload) async {
    final response = await _dio.post('/api/v1/security/enroll', data: payload);
    return SecurityDeviceModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> approveDevice({
    required String deviceId,
    required int adminUserId,
  }) async {
    await _dio.patch(
      '/api/v1/security/enrollments/$deviceId/approve',
      data: {'admin_user_id': adminUserId},
    );
  }

  Future<void> revokeDevice({
    required String deviceId,
    required String reason,
    required int adminUserId,
  }) async {
    await _dio.patch(
      '/api/v1/security/enrollments/$deviceId/revoke',
      queryParameters: {'reason': reason, 'admin_user_id': adminUserId},
    );
  }

  Future<void> heartbeat({required String deviceId}) async {
    await _dio.post('/api/v1/security/enrollments/$deviceId/heartbeat');
  }
}
