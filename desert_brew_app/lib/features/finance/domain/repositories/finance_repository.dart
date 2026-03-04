import '../../domain/entities/income_entry.dart';
import '../../domain/entities/expense_entry.dart';
import '../../domain/entities/balance.dart';

abstract class FinanceRepository {
  Future<List<IncomeEntry>> getIncomes({
    String? category,
    String? profitCenter,
    int? days,
  });
  Future<IncomeSummary> getIncomeSummary({int days = 30});
  Future<IncomeEntry> createIncome(Map<String, dynamic> payload);
  Future<IncomeEntry> updateIncome(int id, Map<String, dynamic> payload);
  Future<void> deleteIncome(int id);
  Future<List<ExpenseEntry>> getExpenses({
    String? category,
    String? expenseType,
    String? profitCenter,
    int? days,
  });
  Future<ExpenseSummary> getExpenseSummary({int days = 30});
  Future<ExpenseEntry> createExpense(Map<String, dynamic> payload);
  Future<ExpenseEntry> updateExpense(int id, Map<String, dynamic> payload);
  Future<void> deleteExpense(int id);
  Future<BalanceSummary> getBalance({int days = 30});
  Future<CashflowReport> getCashflow({int months = 6});
  Future<List<Map<String, dynamic>>> getPricingRules();
  Future<List<Map<String, dynamic>>> getInternalTransfers({
    String? profitCenter,
    String? originType,
    int skip = 0,
    int limit = 100,
  });
  Future<Map<String, dynamic>> getProfitCenterSummary(
    String profitCenter, {
    int days = 30,
  });
}
