import 'package:dio/dio.dart';

import '../../../../core/config/api_config.dart';
import '../../../../core/network/api_client.dart';
import '../models/payroll_employee_model.dart';
import '../models/payroll_entry_model.dart';
import '../models/tip_pool_model.dart';

class PayrollRemoteDataSource {
  PayrollRemoteDataSource() : _dio = ApiClient.forService(ServicePort.payroll);

  final Dio _dio;

  Future<List<PayrollEmployeeModel>> getEmployees({
    String? department,
    String? role,
    String? employmentType,
    bool activeOnly = true,
  }) async {
    final response = await _dio.get(
      '/api/v1/payroll/employees',
      queryParameters: {
        if (department != null) 'department': department,
        if (role != null) 'role': role,
        if (employmentType != null) 'employment_type': employmentType,
        'active_only': activeOnly,
      },
    );

    return (response.data as List<dynamic>)
        .map((e) => PayrollEmployeeModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PayrollEmployeeModel> createEmployee(
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.post(
      '/api/v1/payroll/employees',
      data: payload,
    );
    return PayrollEmployeeModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PayrollEmployeeModel> updateEmployee(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch(
      '/api/v1/payroll/employees/$id',
      data: payload,
    );
    return PayrollEmployeeModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<PayrollEntryModel>> getPayrollEntries({
    int? employeeId,
    String? paymentStatus,
    String? department,
    String? periodType,
    int limit = 50,
  }) async {
    final response = await _dio.get(
      '/api/v1/payroll/entries',
      queryParameters: {
        if (employeeId != null) 'employee_id': employeeId,
        if (paymentStatus != null) 'payment_status': paymentStatus,
        if (department != null) 'department': department,
        if (periodType != null) 'period_type': periodType,
        'limit': limit,
      },
    );

    return (response.data as List<dynamic>)
        .map((e) => PayrollEntryModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PayrollEntryModel> createPayrollEntry(
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.post('/api/v1/payroll/entries', data: payload);
    return PayrollEntryModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PayrollEntryModel> markEntryAsPaid(int entryId) async {
    final response = await _dio.patch('/api/v1/payroll/entries/$entryId/pay');
    return PayrollEntryModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<TipPoolModel>> getTipPools({int limit = 20}) async {
    final response = await _dio.get(
      '/api/v1/payroll/tip-pools',
      queryParameters: {'limit': limit},
    );

    return (response.data as List<dynamic>)
        .map((e) => TipPoolModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TipPoolModel> getTipPool(int id) async {
    final response = await _dio.get('/api/v1/payroll/tip-pools/$id');
    return TipPoolModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<TipPoolModel> createTipPool(Map<String, dynamic> payload) async {
    final response = await _dio.post(
      '/api/v1/payroll/tip-pools',
      data: payload,
    );
    return TipPoolModel.fromJson(response.data as Map<String, dynamic>);
  }
}
