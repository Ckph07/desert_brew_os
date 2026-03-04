import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/finance_remote_datasource.dart';
import '../../data/repositories/finance_repository_impl.dart';
import '../../domain/entities/balance.dart';
import '../bloc/balance/balance_bloc.dart';

class BalanceCashflowPage extends StatelessWidget {
  const BalanceCashflowPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => BalanceBloc(
        FinanceRepositoryImpl(FinanceRemoteDataSource()),
      )..add(BalanceLoadRequested(days: 30, months: 6)),
      child: const _BalanceCashflowView(),
    );
  }
}

class _BalanceCashflowView extends StatelessWidget {
  const _BalanceCashflowView();

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Balance y Cashflow'),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              onPressed: () => context.read<BalanceBloc>()
                  .add(BalanceLoadRequested()),
            ),
          ],
          bottom: const TabBar(tabs: [
            Tab(text: 'Balance'),
            Tab(text: 'Cashflow'),
          ]),
        ),
        body: BlocBuilder<BalanceBloc, BalanceBlocState>(
          builder: (context, state) {
            if (state is BalanceLoading || state is BalanceInitial) {
              return const Center(child: CircularProgressIndicator());
            }
            if (state is BalanceError) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline_rounded,
                        size: 48, color: DesertBrewColors.error),
                    const SizedBox(height: 12),
                    Text(state.message,
                        style: const TextStyle(
                            color: DesertBrewColors.textHint, fontSize: 12),
                        textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => context
                          .read<BalanceBloc>()
                          .add(BalanceLoadRequested()),
                      child: const Text('Reintentar'),
                    ),
                  ],
                ),
              );
            }
            if (state is BalanceLoaded) {
              return TabBarView(
                children: [
                  _BalanceTab(balance: state.balance),
                  _CashflowTab(cashflow: state.cashflow),
                ],
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }
}

// ─── Balance Tab ────────────────────────────────────────────────────────────

class _BalanceTab extends StatelessWidget {
  const _BalanceTab({required this.balance});
  final BalanceSummary balance;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    final profitColor =
        balance.isProfitable ? DesertBrewColors.success : DesertBrewColors.error;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          // ── Net profit KPI ─────────────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: profitColor.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: profitColor.withValues(alpha: 0.3)),
            ),
            child: Column(
              children: [
                Icon(
                  balance.isProfitable
                      ? Icons.trending_up_rounded
                      : Icons.trending_down_rounded,
                  color: profitColor,
                  size: 36,
                ),
                const SizedBox(height: 8),
                Text(
                  currency.format(balance.netProfit),
                  style: TextStyle(
                      color: profitColor,
                      fontSize: 28,
                      fontWeight: FontWeight.bold),
                ),
                Text('Utilidad Neta · ${balance.profitMarginPct.toStringAsFixed(1)}% margen',
                    style: const TextStyle(
                        color: DesertBrewColors.textHint, fontSize: 12)),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // ── Income vs Expenses row ─────────────────────────────────
          Row(
            children: [
              Expanded(
                child: _MetricCard(
                  label: 'Ingresos',
                  amount: balance.totalIncome,
                  color: DesertBrewColors.success,
                  icon: Icons.arrow_downward_rounded,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _MetricCard(
                  label: 'Egresos',
                  amount: balance.totalExpenses,
                  color: DesertBrewColors.error,
                  icon: Icons.arrow_upward_rounded,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // ── Income by category ─────────────────────────────────────
          if (balance.incomeByCategory.isNotEmpty)
            _BreakdownCard(
              title: 'Ingresos por Categoría',
              data: balance.incomeByCategory,
              total: balance.totalIncome,
              color: DesertBrewColors.success,
            ),
          const SizedBox(height: 8),

          // ── Expenses by category ───────────────────────────────────
          if (balance.expensesByCategory.isNotEmpty)
            _BreakdownCard(
              title: 'Egresos por Categoría',
              data: balance.expensesByCategory,
              total: balance.totalExpenses,
              color: DesertBrewColors.error,
            ),
          const SizedBox(height: 8),

          // ── By Profit Center ───────────────────────────────────────
          if (balance.incomeByProfitCenter.isNotEmpty)
            _BreakdownCard(
              title: 'Ingresos por Centro',
              data: balance.incomeByProfitCenter,
              total: balance.totalIncome,
              color: DesertBrewColors.primary,
            ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.amount,
    required this.color,
    required this.icon,
  });
  final String label;
  final double amount;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(height: 6),
          Text(currency.format(amount),
              style: TextStyle(
                  color: color, fontWeight: FontWeight.bold, fontSize: 16)),
          Text(label,
              style: const TextStyle(
                  color: DesertBrewColors.textHint, fontSize: 11)),
        ],
      ),
    );
  }
}

class _BreakdownCard extends StatelessWidget {
  const _BreakdownCard({
    required this.title,
    required this.data,
    required this.total,
    required this.color,
  });
  final String title;
  final Map<String, double> data;
  final double total;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    final sorted = data.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontWeight: FontWeight.bold, fontSize: 12)),
          const SizedBox(height: 8),
          ...sorted.map((e) {
            final pct = total > 0 ? e.value / total : 0.0;
            return Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                children: [
                  SizedBox(
                    width: 90,
                    child: Text(e.key,
                        style: const TextStyle(
                            color: DesertBrewColors.textHint, fontSize: 10),
                        overflow: TextOverflow.ellipsis),
                  ),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: pct,
                        backgroundColor: color.withValues(alpha: 0.1),
                        valueColor: AlwaysStoppedAnimation(color),
                        minHeight: 8,
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(currency.format(e.value),
                      style: const TextStyle(
                          fontSize: 10, color: DesertBrewColors.textSecondary)),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ─── Cashflow Tab ────────────────────────────────────────────────────────────

class _CashflowTab extends StatelessWidget {
  const _CashflowTab({required this.cashflow});
  final CashflowReport cashflow;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    final maxVal = cashflow.months.isEmpty
        ? 1.0
        : cashflow.months
            .map((m) => [m.income, m.expenses].reduce((a, b) => a > b ? a : b))
            .reduce((a, b) => a > b ? a : b);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          // ── Total KPIs ─────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: DesertBrewColors.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                _KpiCell(currency.format(cashflow.totalIncome), 'Ingresos',
                    DesertBrewColors.success),
                _KpiCell(currency.format(cashflow.totalExpenses), 'Egresos',
                    DesertBrewColors.error),
                _KpiCell(
                  currency.format(cashflow.totalNet),
                  'Neto',
                  cashflow.totalNet >= 0
                      ? DesertBrewColors.success
                      : DesertBrewColors.error,
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // ── Monthly bars ───────────────────────────────────────────
          ...cashflow.months.map((month) {
            final incomePct = maxVal > 0 ? month.income / maxVal : 0.0;
            final expensesPct = maxVal > 0 ? month.expenses / maxVal : 0.0;
            final netColor = month.isPositive
                ? DesertBrewColors.success
                : DesertBrewColors.error;
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: DesertBrewColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: netColor.withValues(alpha: 0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(month.month,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 13)),
                      Text(currency.format(month.net),
                          style: TextStyle(
                              color: netColor,
                              fontWeight: FontWeight.bold,
                              fontSize: 12)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  // Income bar
                  Row(
                    children: [
                      const SizedBox(
                          width: 60,
                          child: Text('Ingreso',
                              style: TextStyle(
                                  color: DesertBrewColors.textHint,
                                  fontSize: 9))),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: incomePct,
                            backgroundColor:
                                DesertBrewColors.success.withValues(alpha: 0.1),
                            valueColor: const AlwaysStoppedAnimation(
                                DesertBrewColors.success),
                            minHeight: 8,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(currency.format(month.income),
                          style: const TextStyle(
                              color: DesertBrewColors.success, fontSize: 9)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  // Expenses bar
                  Row(
                    children: [
                      const SizedBox(
                          width: 60,
                          child: Text('Egreso',
                              style: TextStyle(
                                  color: DesertBrewColors.textHint,
                                  fontSize: 9))),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: expensesPct,
                            backgroundColor:
                                DesertBrewColors.error.withValues(alpha: 0.1),
                            valueColor: const AlwaysStoppedAnimation(
                                DesertBrewColors.error),
                            minHeight: 8,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(currency.format(month.expenses),
                          style: const TextStyle(
                              color: DesertBrewColors.error, fontSize: 9)),
                    ],
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

class _KpiCell extends StatelessWidget {
  const _KpiCell(this.value, this.label, this.color);
  final String value;
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => Expanded(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(value,
                style: TextStyle(
                    color: color, fontWeight: FontWeight.bold, fontSize: 12),
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center),
            Text(label,
                style: const TextStyle(
                    color: DesertBrewColors.textHint, fontSize: 9),
                textAlign: TextAlign.center),
          ],
        ),
      );
}
