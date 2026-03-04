import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/production_remote_datasource.dart';
import '../../data/repositories/production_repository_impl.dart';
import '../../domain/entities/cost_entities.dart';
import '../bloc/costs/costs_bloc.dart';

class CostManagementPage extends StatelessWidget {
  const CostManagementPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              CostsBloc(ProductionRepositoryImpl(ProductionRemoteDataSource()))
                ..add(CostsLoadRequested()),
      child: const _CostView(),
    );
  }
}

class _CostView extends StatelessWidget {
  const _CostView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestión de Costos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () => context.read<CostsBloc>().add(CostsLoadRequested()),
          ),
        ],
      ),
      body: BlocBuilder<CostsBloc, CostsState>(
        builder: (context, state) {
          if (state is CostsLoading || state is CostsInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is CostsError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.error_outline_rounded,
                    size: 48,
                    color: DesertBrewColors.error,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    state.message,
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed:
                        () =>
                            context.read<CostsBloc>().add(CostsLoadRequested()),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }
          if (state is CostsLoaded) {
            return _CostBody(
              summary: state.summary,
              fixedCosts: state.fixedCosts,
              ingredientPrices: state.ingredientPrices,
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}

class _CostBody extends StatelessWidget {
  const _CostBody({
    required this.summary,
    required this.fixedCosts,
    required this.ingredientPrices,
  });

  final CostSummary summary;
  final List<FixedMonthlyCost> fixedCosts;
  final List<IngredientPrice> ingredientPrices;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final activeFixed = fixedCosts.where((f) => f.isActive).toList();
    final activeIngredients =
        ingredientPrices.where((p) => p.isActive).toList();

    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          // KPI summary bar
          Container(
            color: DesertBrewColors.surface,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                _SummaryKpi(
                  '\$${summary.fixedCostPerLiter.toStringAsFixed(2)}/L',
                  'Costo Fijo/L',
                  DesertBrewColors.primary,
                ),
                const SizedBox(width: 8),
                _SummaryKpi(
                  currency.format(summary.totalFixedMonthly),
                  'Total Mensual',
                  DesertBrewColors.accent,
                ),
                const SizedBox(width: 8),
                _SummaryKpi(
                  '${summary.targetLiters.toStringAsFixed(0)} L',
                  'Meta Mensual',
                  DesertBrewColors.success,
                ),
              ],
            ),
          ),

          // Tabs
          const TabBar(
            tabs: [
              Tab(text: 'Resumen'),
              Tab(text: 'Costos Fijos'),
              Tab(text: 'Ingredientes'),
            ],
            labelStyle: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
          ),

          Expanded(
            child: TabBarView(
              children: [
                // Tab 1: Breakdown by category
                _SummaryTab(summary: summary, currency: currency),

                // Tab 2: Fixed costs list
                _FixedCostsTab(costs: activeFixed, currency: currency),

                // Tab 3: Ingredient prices list
                _IngredientsTab(prices: activeIngredients, currency: currency),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Tab 1: Summary ────────────────────────────────────────────────────────────
class _SummaryTab extends StatelessWidget {
  const _SummaryTab({required this.summary, required this.currency});
  final CostSummary summary;
  final NumberFormat currency;

  @override
  Widget build(BuildContext context) {
    final breakdown = summary.costBreakdown;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Desglose por Categoría',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: DesertBrewColors.textSecondary,
            fontSize: 13,
          ),
        ),
        const SizedBox(height: 12),
        ...breakdown.map((item) {
          final cat = item['category'] as String? ?? '';
          final amount =
              ((item['monthly_amount'] ?? item['total_amount']) as num?)
                  ?.toDouble() ??
              0;
          final pct =
              summary.totalFixedMonthly > 0
                  ? amount / summary.totalFixedMonthly
                  : 0.0;
          return _CategoryRow(
            category: cat,
            amount: amount,
            pct: pct,
            currency: currency,
          );
        }),
        const Divider(height: 24),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Total Fijo Mensual',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              currency.format(summary.totalFixedMonthly),
              style: const TextStyle(
                color: DesertBrewColors.primary,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
        if (summary.ingredientTotalEstimated != null) ...[
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Ingredientes (estimado)',
                style: TextStyle(
                  color: DesertBrewColors.textHint,
                  fontSize: 12,
                ),
              ),
              Text(
                currency.format(summary.ingredientTotalEstimated),
                style: const TextStyle(
                  color: DesertBrewColors.accent,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}

class _CategoryRow extends StatelessWidget {
  const _CategoryRow({
    required this.category,
    required this.amount,
    required this.pct,
    required this.currency,
  });

  final String category;
  final double amount;
  final double pct;
  final NumberFormat currency;

  static const _catColors = {
    'FUEL': Color(0xFFF97316),
    'ENERGY': Color(0xFFF59E0B),
    'WATER': Color(0xFF3B82F6),
    'HR': Color(0xFF8B5CF6),
    'OPERATIONS': Color(0xFF10B981),
    'GAS_CO2': Color(0xFF06B6D4),
    'COMMS': Color(0xFFEC4899),
    'VEHICLE': Color(0xFF6366F1),
    'OTHER': DesertBrewColors.textHint,
  };

  Color get _color => _catColors[category] ?? DesertBrewColors.primary;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(category, style: const TextStyle(fontSize: 12)),
              ),
              Text(
                currency.format(amount),
                style: TextStyle(
                  color: _color,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Stack(
            children: [
              Container(
                height: 6,
                decoration: BoxDecoration(
                  color: DesertBrewColors.surface,
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
              FractionallySizedBox(
                widthFactor: pct.clamp(0.0, 1.0),
                child: Container(
                  height: 6,
                  decoration: BoxDecoration(
                    color: _color,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Tab 2: Fixed Costs ────────────────────────────────────────────────────────
class _FixedCostsTab extends StatelessWidget {
  const _FixedCostsTab({required this.costs, required this.currency});
  final List<FixedMonthlyCost> costs;
  final NumberFormat currency;

  @override
  Widget build(BuildContext context) {
    if (costs.isEmpty) {
      return const Center(
        child: Text(
          'Sin costos fijos registrados',
          style: TextStyle(color: DesertBrewColors.textHint),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: costs.length,
      itemBuilder: (_, i) {
        final c = costs[i];
        return ListTile(
          dense: true,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 4,
          ),
          tileColor: DesertBrewColors.surface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          title: Text(c.concept, style: const TextStyle(fontSize: 13)),
          subtitle: Text(
            c.category,
            style: const TextStyle(
              color: DesertBrewColors.textHint,
              fontSize: 11,
            ),
          ),
          trailing: Text(
            currency.format(c.monthlyAmount),
            style: const TextStyle(
              color: DesertBrewColors.primary,
              fontWeight: FontWeight.bold,
            ),
          ),
        );
      },
    );
  }
}

// ── Tab 3: Ingredient Prices ──────────────────────────────────────────────────
class _IngredientsTab extends StatelessWidget {
  const _IngredientsTab({required this.prices, required this.currency});
  final List<IngredientPrice> prices;
  final NumberFormat currency;

  static const _catColors = {
    'MALT': Color(0xFFF59E0B),
    'HOP': Color(0xFF10B981),
    'YEAST': Color(0xFF8B5CF6),
    'ADJUNCT': Color(0xFFF97316),
    'CHEMICAL': Color(0xFF3B82F6),
    'PACKAGING': Color(0xFF06B6D4),
    'OTHER': DesertBrewColors.textHint,
  };

  @override
  Widget build(BuildContext context) {
    if (prices.isEmpty) {
      return const Center(
        child: Text(
          'Sin precios de ingredientes registrados',
          style: TextStyle(color: DesertBrewColors.textHint),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: prices.length,
      itemBuilder: (_, i) {
        final p = prices[i];
        final color = _catColors[p.category] ?? DesertBrewColors.primary;
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: DesertBrewColors.surface,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: color.withValues(alpha: 0.2)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  p.category,
                  style: TextStyle(
                    color: color,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(p.name, style: const TextStyle(fontSize: 13)),
                    if (p.supplierName != null)
                      Text(
                        p.supplierName!,
                        style: const TextStyle(
                          color: DesertBrewColors.textHint,
                          fontSize: 11,
                        ),
                      ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${p.currency} ${p.currentPrice.toStringAsFixed(2)}',
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                  Text(
                    '/${p.unitMeasure}',
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _SummaryKpi extends StatelessWidget {
  const _SummaryKpi(this.value, this.label, this.color);
  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
            ),
            Text(
              label,
              style: const TextStyle(
                color: DesertBrewColors.textHint,
                fontSize: 10,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
