import '../../domain/entities/income_entry.dart';
import '../../domain/entities/expense_entry.dart';
import '../../domain/entities/balance.dart';
import '../../domain/repositories/finance_repository.dart';
import '../datasources/finance_remote_datasource.dart';

class FinanceRepositoryImpl implements FinanceRepository {
  FinanceRepositoryImpl(this._remote);
  final FinanceRemoteDataSource _remote;

  @override
  Future<List<IncomeEntry>> getIncomes({
    String? category,
    String? profitCenter,
    int? days,
  }) => _remote.getIncomes(
    category: category,
    profitCenter: profitCenter,
    days: days,
  );

  @override
  Future<IncomeSummary> getIncomeSummary({int days = 30}) =>
      _remote.getIncomeSummary(days: days);

  @override
  Future<IncomeEntry> createIncome(Map<String, dynamic> payload) =>
      _remote.createIncome(payload);

  @override
  Future<IncomeEntry> updateIncome(int id, Map<String, dynamic> payload) =>
      _remote.updateIncome(id, payload);

  @override
  Future<void> deleteIncome(int id) => _remote.deleteIncome(id);

  @override
  Future<List<ExpenseEntry>> getExpenses({
    String? category,
    String? expenseType,
    String? profitCenter,
    int? days,
  }) => _remote.getExpenses(
    category: category,
    expenseType: expenseType,
    profitCenter: profitCenter,
    days: days,
  );

  @override
  Future<ExpenseSummary> getExpenseSummary({int days = 30}) =>
      _remote.getExpenseSummary(days: days);

  @override
  Future<ExpenseEntry> createExpense(Map<String, dynamic> payload) =>
      _remote.createExpense(payload);

  @override
  Future<ExpenseEntry> updateExpense(int id, Map<String, dynamic> payload) =>
      _remote.updateExpense(id, payload);

  @override
  Future<void> deleteExpense(int id) => _remote.deleteExpense(id);

  @override
  Future<BalanceSummary> getBalance({int days = 30}) =>
      _remote.getBalance(days: days);

  @override
  Future<CashflowReport> getCashflow({int months = 6}) =>
      _remote.getCashflow(months: months);

  @override
  Future<List<Map<String, dynamic>>> getPricingRules() =>
      _remote.getPricingRules();

  @override
  Future<List<Map<String, dynamic>>> getInternalTransfers({
    String? profitCenter,
    String? originType,
    int skip = 0,
    int limit = 100,
  }) => _remote.getInternalTransfers(
    profitCenter: profitCenter,
    originType: originType,
    skip: skip,
    limit: limit,
  );

  @override
  Future<Map<String, dynamic>> getProfitCenterSummary(
    String profitCenter, {
    int days = 30,
  }) => _remote.getProfitCenterSummary(profitCenter, days: days);
}
