import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/config/api_config.dart';
import '../models/finance_models.dart';

/// All HTTP calls to Finance Service on :8005.
class FinanceRemoteDataSource {
  FinanceRemoteDataSource() : _dio = ApiClient.forService(ServicePort.finance);

  final Dio _dio;

  // ── Income ─────────────────────────────────────────────────────────────

  Future<List<IncomeEntryModel>> getIncomes({
    String? category,
    String? profitCenter,
    int? days,
    int skip = 0,
    int limit = 100,
  }) async {
    final res = await _dio.get(
      '/api/v1/finance/incomes',
      queryParameters: {
        if (category != null) 'category': category,
        if (profitCenter != null) 'profit_center': profitCenter,
        if (days != null) 'days': days,
        'skip': skip,
        'limit': limit,
      },
    );
    return (res.data as List<dynamic>)
        .map((e) => IncomeEntryModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<IncomeSummaryModel> getIncomeSummary({int days = 30}) async {
    final res = await _dio.get(
      '/api/v1/finance/incomes/summary',
      queryParameters: {'days': days},
    );
    return IncomeSummaryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<IncomeEntryModel> createIncome(Map<String, dynamic> payload) async {
    final res = await _dio.post('/api/v1/finance/incomes', data: payload);
    return IncomeEntryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<IncomeEntryModel> updateIncome(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final res = await _dio.patch('/api/v1/finance/incomes/$id', data: payload);
    return IncomeEntryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteIncome(int id) async {
    await _dio.delete('/api/v1/finance/incomes/$id');
  }

  // ── Expenses ────────────────────────────────────────────────────────────

  Future<List<ExpenseEntryModel>> getExpenses({
    String? category,
    String? expenseType,
    String? profitCenter,
    int? days,
    int skip = 0,
    int limit = 100,
  }) async {
    final res = await _dio.get(
      '/api/v1/finance/expenses',
      queryParameters: {
        if (category != null) 'category': category,
        if (expenseType != null) 'expense_type': expenseType,
        if (profitCenter != null) 'profit_center': profitCenter,
        if (days != null) 'days': days,
        'skip': skip,
        'limit': limit,
      },
    );
    return (res.data as List<dynamic>)
        .map((e) => ExpenseEntryModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ExpenseSummaryModel> getExpenseSummary({int days = 30}) async {
    final res = await _dio.get(
      '/api/v1/finance/expenses/summary',
      queryParameters: {'days': days},
    );
    return ExpenseSummaryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ExpenseEntryModel> createExpense(Map<String, dynamic> payload) async {
    final res = await _dio.post('/api/v1/finance/expenses', data: payload);
    return ExpenseEntryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ExpenseEntryModel> updateExpense(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final res = await _dio.patch('/api/v1/finance/expenses/$id', data: payload);
    return ExpenseEntryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteExpense(int id) async {
    await _dio.delete('/api/v1/finance/expenses/$id');
  }

  // ── Balance & Cashflow ──────────────────────────────────────────────────

  Future<BalanceSummaryModel> getBalance({int days = 30}) async {
    final res = await _dio.get(
      '/api/v1/finance/balance',
      queryParameters: {'days': days},
    );
    return BalanceSummaryModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<CashflowReportModel> getCashflow({int months = 6}) async {
    final res = await _dio.get(
      '/api/v1/finance/cashflow',
      queryParameters: {'months': months},
    );
    return CashflowReportModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Map<String, dynamic>>> getPricingRules() async {
    final res = await _dio.get('/api/v1/finance/pricing-rules');
    return (res.data as List<dynamic>).cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> getInternalTransfers({
    String? profitCenter,
    String? originType,
    int skip = 0,
    int limit = 100,
  }) async {
    final res = await _dio.get(
      '/api/v1/finance/internal-transfers',
      queryParameters: {
        if (profitCenter != null) 'profit_center': profitCenter,
        if (originType != null) 'origin_type': originType,
        'skip': skip,
        'limit': limit,
      },
    );
    return (res.data as List<dynamic>).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getProfitCenterSummary(
    String profitCenter, {
    int days = 30,
  }) async {
    final res = await _dio.get(
      '/api/v1/finance/profit-center/$profitCenter/summary',
      queryParameters: {'days': days},
    );
    return res.data as Map<String, dynamic>;
  }
}
