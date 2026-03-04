import '../../domain/entities/income_entry.dart';
import '../../domain/entities/expense_entry.dart';
import '../../domain/entities/balance.dart';

class IncomeEntryModel extends IncomeEntry {
  const IncomeEntryModel({
    required super.id, required super.incomeType, required super.category,
    required super.description, required super.amount, required super.paymentMethod,
    required super.profitCenter, required super.receivedDate, required super.createdAt,
    super.referenceId, super.receivedBy, super.notes,
  });

  factory IncomeEntryModel.fromJson(Map<String, dynamic> j) => IncomeEntryModel(
    id: (j['id'] as num).toInt(),
    incomeType: j['income_type'] as String,
    category: j['category'] as String,
    description: j['description'] as String,
    amount: (j['amount'] as num).toDouble(),
    paymentMethod: j['payment_method'] as String,
    profitCenter: j['profit_center'] as String,
    receivedDate: DateTime.parse(j['received_date'] as String),
    createdAt: DateTime.parse(j['created_at'] as String),
    referenceId: j['reference_id'] as String?,
    receivedBy: j['received_by'] as String?,
    notes: j['notes'] as String?,
  );
}

class IncomeSummaryModel extends IncomeSummary {
  const IncomeSummaryModel({
    required super.periodStart, required super.periodEnd,
    required super.totalIncome, required super.count,
    required super.byCategory, required super.byPaymentMethod,
    required super.byProfitCenter,
  });

  factory IncomeSummaryModel.fromJson(Map<String, dynamic> j) => IncomeSummaryModel(
    periodStart: DateTime.parse(j['period_start'] as String),
    periodEnd: DateTime.parse(j['period_end'] as String),
    totalIncome: (j['total_income'] as num).toDouble(),
    count: (j['count'] as num).toInt(),
    byCategory: _toDoubleMap(j['by_category']),
    byPaymentMethod: _toDoubleMap(j['by_payment_method']),
    byProfitCenter: _toDoubleMap(j['by_profit_center']),
  );
}

class ExpenseEntryModel extends ExpenseEntry {
  const ExpenseEntryModel({
    required super.id, required super.expenseType, required super.category,
    required super.description, required super.amount, required super.paymentMethod,
    required super.profitCenter, required super.paidDate, required super.createdAt,
    super.referenceId, super.supplierName, super.paidBy, super.notes,
  });

  factory ExpenseEntryModel.fromJson(Map<String, dynamic> j) => ExpenseEntryModel(
    id: (j['id'] as num).toInt(),
    expenseType: j['expense_type'] as String,
    category: j['category'] as String,
    description: j['description'] as String,
    amount: (j['amount'] as num).toDouble(),
    paymentMethod: j['payment_method'] as String,
    profitCenter: j['profit_center'] as String,
    paidDate: DateTime.parse(j['paid_date'] as String),
    createdAt: DateTime.parse(j['created_at'] as String),
    referenceId: j['reference_id'] as String?,
    supplierName: j['supplier_name'] as String?,
    paidBy: j['paid_by'] as String?,
    notes: j['notes'] as String?,
  );
}

class ExpenseSummaryModel extends ExpenseSummary {
  const ExpenseSummaryModel({
    required super.periodStart, required super.periodEnd,
    required super.totalExpenses, required super.count,
    required super.byCategory, required super.byType,
    required super.byProfitCenter,
  });

  factory ExpenseSummaryModel.fromJson(Map<String, dynamic> j) => ExpenseSummaryModel(
    periodStart: DateTime.parse(j['period_start'] as String),
    periodEnd: DateTime.parse(j['period_end'] as String),
    totalExpenses: (j['total_expenses'] as num).toDouble(),
    count: (j['count'] as num).toInt(),
    byCategory: _toDoubleMap(j['by_category']),
    byType: _toDoubleMap(j['by_type']),
    byProfitCenter: _toDoubleMap(j['by_profit_center']),
  );
}

class BalanceSummaryModel extends BalanceSummary {
  const BalanceSummaryModel({
    required super.periodStart, required super.periodEnd,
    required super.totalIncome, required super.totalExpenses,
    required super.netProfit, required super.profitMarginPct,
    required super.incomeByCategory, required super.expensesByCategory,
    required super.incomeByProfitCenter, required super.expensesByProfitCenter,
  });

  factory BalanceSummaryModel.fromJson(Map<String, dynamic> j) => BalanceSummaryModel(
    periodStart: DateTime.parse(j['period_start'] as String),
    periodEnd: DateTime.parse(j['period_end'] as String),
    totalIncome: (j['total_income'] as num).toDouble(),
    totalExpenses: (j['total_expenses'] as num).toDouble(),
    netProfit: (j['net_profit'] as num).toDouble(),
    profitMarginPct: (j['profit_margin_percentage'] as num).toDouble(),
    incomeByCategory: _toDoubleMap(j['income_by_category']),
    expensesByCategory: _toDoubleMap(j['expenses_by_category']),
    incomeByProfitCenter: _toDoubleMap(j['income_by_profit_center']),
    expensesByProfitCenter: _toDoubleMap(j['expenses_by_profit_center']),
  );
}

class CashflowReportModel extends CashflowReport {
  const CashflowReportModel({
    required super.periodStart, required super.periodEnd,
    required super.months, required super.totalIncome,
    required super.totalExpenses, required super.totalNet,
  });

  factory CashflowReportModel.fromJson(Map<String, dynamic> j) => CashflowReportModel(
    periodStart: DateTime.parse(j['period_start'] as String),
    periodEnd: DateTime.parse(j['period_end'] as String),
    months: (j['months'] as List<dynamic>)
        .map((m) => CashflowMonth(
              month: m['month'] as String,
              income: (m['income'] as num).toDouble(),
              expenses: (m['expenses'] as num).toDouble(),
              net: (m['net'] as num).toDouble(),
            ))
        .toList(),
    totalIncome: (j['total_income'] as num).toDouble(),
    totalExpenses: (j['total_expenses'] as num).toDouble(),
    totalNet: (j['total_net'] as num).toDouble(),
  );
}

Map<String, double> _toDoubleMap(dynamic raw) {
  if (raw == null) return {};
  return (raw as Map<String, dynamic>)
      .map((k, v) => MapEntry(k, (v as num).toDouble()));
}
