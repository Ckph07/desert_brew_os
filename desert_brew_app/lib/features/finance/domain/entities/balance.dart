import 'package:equatable/equatable.dart';

/// One month in the cashflow report.
class CashflowMonth extends Equatable {
  const CashflowMonth({
    required this.month,
    required this.income,
    required this.expenses,
    required this.net,
  });

  final String month; // "2026-02"
  final double income;
  final double expenses;
  final double net;

  bool get isPositive => net >= 0;

  @override
  List<Object?> get props => [month, net];
}

/// Full cashflow report (N months).
class CashflowReport extends Equatable {
  const CashflowReport({
    required this.periodStart,
    required this.periodEnd,
    required this.months,
    required this.totalIncome,
    required this.totalExpenses,
    required this.totalNet,
  });

  final DateTime periodStart;
  final DateTime periodEnd;
  final List<CashflowMonth> months;
  final double totalIncome;
  final double totalExpenses;
  final double totalNet;

  @override
  List<Object?> get props => [totalNet];
}

/// Consolidated balance for a period.
class BalanceSummary extends Equatable {
  const BalanceSummary({
    required this.periodStart,
    required this.periodEnd,
    required this.totalIncome,
    required this.totalExpenses,
    required this.netProfit,
    required this.profitMarginPct,
    required this.incomeByCategory,
    required this.expensesByCategory,
    required this.incomeByProfitCenter,
    required this.expensesByProfitCenter,
  });

  final DateTime periodStart;
  final DateTime periodEnd;
  final double totalIncome;
  final double totalExpenses;
  final double netProfit;
  final double profitMarginPct;
  final Map<String, double> incomeByCategory;
  final Map<String, double> expensesByCategory;
  final Map<String, double> incomeByProfitCenter;
  final Map<String, double> expensesByProfitCenter;

  bool get isProfitable => netProfit >= 0;

  @override
  List<Object?> get props => [netProfit, profitMarginPct];
}
