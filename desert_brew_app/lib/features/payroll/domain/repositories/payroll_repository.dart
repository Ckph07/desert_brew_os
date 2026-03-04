import '../entities/payroll_employee.dart';
import '../entities/payroll_entry.dart';
import '../entities/tip_pool.dart';

abstract class PayrollRepository {
  Future<List<PayrollEmployee>> getEmployees({
    String? department,
    String? role,
    String? employmentType,
    bool activeOnly = true,
  });

  Future<PayrollEmployee> createEmployee(Map<String, dynamic> payload);
  Future<PayrollEmployee> updateEmployee(int id, Map<String, dynamic> payload);

  Future<List<PayrollEntry>> getPayrollEntries({
    int? employeeId,
    String? paymentStatus,
    String? department,
    String? periodType,
    int limit = 50,
  });

  Future<PayrollEntry> createPayrollEntry(Map<String, dynamic> payload);
  Future<PayrollEntry> markEntryAsPaid(int entryId);

  Future<List<TipPool>> getTipPools({int limit = 20});
  Future<TipPool> getTipPool(int id);
  Future<TipPool> createTipPool(Map<String, dynamic> payload);
}
