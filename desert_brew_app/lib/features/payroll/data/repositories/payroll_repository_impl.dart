import '../../domain/entities/payroll_employee.dart';
import '../../domain/entities/payroll_entry.dart';
import '../../domain/entities/tip_pool.dart';
import '../../domain/repositories/payroll_repository.dart';
import '../datasources/payroll_remote_datasource.dart';

class PayrollRepositoryImpl implements PayrollRepository {
  PayrollRepositoryImpl(this._remote);

  final PayrollRemoteDataSource _remote;

  @override
  Future<List<PayrollEmployee>> getEmployees({
    String? department,
    String? role,
    String? employmentType,
    bool activeOnly = true,
  }) => _remote.getEmployees(
    department: department,
    role: role,
    employmentType: employmentType,
    activeOnly: activeOnly,
  );

  @override
  Future<PayrollEmployee> createEmployee(Map<String, dynamic> payload) =>
      _remote.createEmployee(payload);

  @override
  Future<PayrollEmployee> updateEmployee(
    int id,
    Map<String, dynamic> payload,
  ) => _remote.updateEmployee(id, payload);

  @override
  Future<List<PayrollEntry>> getPayrollEntries({
    int? employeeId,
    String? paymentStatus,
    String? department,
    String? periodType,
    int limit = 50,
  }) => _remote.getPayrollEntries(
    employeeId: employeeId,
    paymentStatus: paymentStatus,
    department: department,
    periodType: periodType,
    limit: limit,
  );

  @override
  Future<PayrollEntry> createPayrollEntry(Map<String, dynamic> payload) =>
      _remote.createPayrollEntry(payload);

  @override
  Future<PayrollEntry> markEntryAsPaid(int entryId) =>
      _remote.markEntryAsPaid(entryId);

  @override
  Future<List<TipPool>> getTipPools({int limit = 20}) =>
      _remote.getTipPools(limit: limit);

  @override
  Future<TipPool> getTipPool(int id) => _remote.getTipPool(id);

  @override
  Future<TipPool> createTipPool(Map<String, dynamic> payload) =>
      _remote.createTipPool(payload);
}
