import 'package:dio/dio.dart';

import '../../../../core/config/api_config.dart';
import '../../../../core/network/api_client.dart';
import '../../domain/entities/global_kpi_snapshot.dart';

class DashboardRemoteDataSource {
  DashboardRemoteDataSource()
    : _inventory = ApiClient.forService(ServicePort.inventory),
      _sales = ApiClient.forService(ServicePort.sales),
      _production = ApiClient.forService(ServicePort.production),
      _payroll = ApiClient.forService(ServicePort.payroll),
      _security = ApiClient.forService(ServicePort.security);

  final Dio _inventory;
  final Dio _sales;
  final Dio _production;
  final Dio _payroll;
  final Dio _security;

  String? _inventorySummaryPath;

  Future<GlobalKpiSnapshot> fetchGlobalKpis() async {
    final now = DateTime.now();
    final startOfMonth = DateTime(now.year, now.month, 1);

    final responses = await Future.wait<dynamic>([
      _fetchInventorySummaryRows(),
      _production.get(
        '/api/v1/production/batches',
        queryParameters: {'limit': 200, 'skip': 0},
      ),
      _sales.get(
        '/api/v1/sales/notes',
        queryParameters: {'limit': 500, 'offset': 0},
      ),
      _inventory.get(
        '/api/v1/inventory/kegs',
        queryParameters: {'state': 'IN_CLIENT', 'limit': 500, 'skip': 0},
      ),
      _payroll.get(
        '/api/v1/payroll/entries',
        queryParameters: {'payment_status': 'PENDING', 'limit': 500},
      ),
      _security.get('/api/v1/security/enrollments/stats'),
    ]);

    final inventoryRows = responses[0] as List<Map<String, dynamic>>;
    final batchData = (responses[1] as Response).data as List<dynamic>;
    final noteData = (responses[2] as Response).data as List<dynamic>;
    final kegData = (responses[3] as Response).data as List<dynamic>;
    final payrollData = (responses[4] as Response).data as List<dynamic>;
    final securityStats =
        (responses[5] as Response).data as Map<String, dynamic>;

    final inventoryValue = inventoryRows.fold<double>(0, (sum, row) {
      final value = row['total_value_mxn'] ?? row['total_value'] ?? 0;
      if (value is num) return sum + value.toDouble();
      return sum + (double.tryParse(value.toString()) ?? 0);
    });

    const activeBatchStates = {
      'BREWING',
      'FERMENTING',
      'CONDITIONING',
      'PACKAGING',
    };
    final activeBatches =
        batchData.where((item) {
          final status =
              (item as Map<String, dynamic>)['status']
                  ?.toString()
                  .toUpperCase();
          return activeBatchStates.contains(status);
        }).length;

    final monthNotes =
        noteData.where((item) {
          final map = item as Map<String, dynamic>;
          final raw = map['created_at'];
          if (raw == null) return false;
          final createdAt = DateTime.tryParse(raw.toString());
          return createdAt != null &&
              !createdAt.isBefore(startOfMonth) &&
              createdAt.isBefore(now.add(const Duration(days: 1)));
        }).length;

    final activeDevices =
        ((securityStats['by_status'] as Map<String, dynamic>? ??
                    const {})['active']
                as num?)
            ?.toInt() ??
        0;

    return GlobalKpiSnapshot(
      inventoryValueMxn: inventoryValue,
      activeBatches: activeBatches,
      monthlySalesNotes: monthNotes,
      kegsInClient: kegData.length,
      pendingPayrollEntries: payrollData.length,
      activeDevices: activeDevices,
      fetchedAt: now,
    );
  }

  Future<List<Map<String, dynamic>>> _fetchInventorySummaryRows() async {
    Future<List<Map<String, dynamic>>> fetchFrom(String path) async {
      final response = await _inventory.get(path);
      final rows = response.data as List<dynamic>;
      return rows.cast<Map<String, dynamic>>();
    }

    if (_inventorySummaryPath != null) {
      return fetchFrom(_inventorySummaryPath!);
    }

    try {
      final data = await fetchFrom('/api/v1/inventory/summary');
      _inventorySummaryPath = '/api/v1/inventory/summary';
      return data;
    } on DioException catch (error) {
      if (error.response?.statusCode != 404) rethrow;
      final data = await fetchFrom('/api/v1/inventory/stock/summary');
      _inventorySummaryPath = '/api/v1/inventory/stock/summary';
      return data;
    }
  }
}
