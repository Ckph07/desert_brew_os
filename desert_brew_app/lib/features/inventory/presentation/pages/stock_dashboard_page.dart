import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/inventory_remote_datasource.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/stock_batch.dart';
import '../bloc/stock/stock_bloc.dart';

class StockDashboardPage extends StatelessWidget {
  const StockDashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              StockBloc(InventoryRepositoryImpl(InventoryRemoteDataSource()))
                ..add(StockLoadRequested()),
      child: const _StockDashboardView(),
    );
  }
}

enum _StockListViewMode { batches, supplies }

class _StockDashboardView extends StatefulWidget {
  const _StockDashboardView();

  @override
  State<_StockDashboardView> createState() => _StockDashboardViewState();
}

class _StockDashboardViewState extends State<_StockDashboardView> {
  _StockListViewMode _viewMode = _StockListViewMode.batches;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inventario'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () => context.read<StockBloc>().add(StockRefreshRequested()),
          ),
          IconButton(
            icon: const Icon(Icons.list_alt_rounded),
            tooltip: 'Insumos',
            onPressed: () => context.push('/inventory/ingredients'),
          ),
          IconButton(
            icon: const Icon(Icons.people_rounded),
            tooltip: 'Proveedores',
            onPressed: () => context.push('/inventory/suppliers'),
          ),
        ],
      ),
      body: BlocBuilder<StockBloc, StockState>(
        builder: (context, state) {
          if (state is StockLoading || state is StockInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is StockError) {
            return _ErrorView(message: state.message);
          }
          if (state is StockLoaded || state is StockReceiving) {
            final batches =
                state is StockLoaded
                    ? state.batches
                    : (state as StockReceiving).batches;
            final summary =
                state is StockLoaded
                    ? state.summary
                    : (state as StockReceiving).summary;
            final supplies = _StockSupplyItem.fromBatches(batches);

            return Column(
              children: [
                // ── KPI Summary Bar ──────────────────────────────────
                _SummaryBar(
                  totalBatches: summary.totalBatches,
                  totalValue: summary.totalValue,
                  lowStockItems: summary.lowStockItems,
                ),
                // ── Filter Chips ─────────────────────────────────────
                _CategoryFilter(
                  selected: state is StockLoaded ? state.filterCategory : null,
                ),
                _ListModeToggle(
                  selectedMode: _viewMode,
                  batchesCount: batches.length,
                  suppliesCount: supplies.length,
                  onModeChanged: (mode) => setState(() => _viewMode = mode),
                ),
                // ── Stock List ───────────────────────────────────────
                Expanded(
                  child:
                      _viewMode == _StockListViewMode.batches
                          ? batches.isEmpty
                              ? const _EmptyState(
                                viewMode: _StockListViewMode.batches,
                              )
                              : ListView.builder(
                                padding: const EdgeInsets.all(8),
                                itemCount: batches.length,
                                itemBuilder:
                                    (_, i) =>
                                        _StockBatchTile(batch: batches[i]),
                              )
                          : supplies.isEmpty
                          ? const _EmptyState(
                            viewMode: _StockListViewMode.supplies,
                          )
                          : ListView.builder(
                            padding: const EdgeInsets.all(8),
                            itemCount: supplies.length,
                            itemBuilder:
                                (_, i) => _StockSupplyTile(item: supplies[i]),
                          ),
                ),
              ],
            );
          }
          if (state is StockReceiveSuccess) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.check_circle_rounded,
                    color: DesertBrewColors.success,
                    size: 64,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '✓ ${state.newBatch.ingredientName} recibido',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(
                    '${state.newBatch.quantity} ${state.newBatch.unit}'
                    ' @ \$${state.newBatch.unitCost}/u',
                    style: const TextStyle(
                      color: DesertBrewColors.textSecondary,
                    ),
                  ),
                ],
              ),
            );
          }
          return const SizedBox.shrink();
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/inventory/receive'),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Recibir Stock'),
      ),
    );
  }
}

// ── KPI Summary Bar ────────────────────────────────────────────────────────

class _SummaryBar extends StatelessWidget {
  const _SummaryBar({
    required this.totalBatches,
    required this.totalValue,
    required this.lowStockItems,
  });
  final int totalBatches;
  final double totalValue;
  final int lowStockItems;

  @override
  Widget build(BuildContext context) {
    final fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return Container(
      color: DesertBrewColors.surface,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _KpiChip(
            label: 'Lotes',
            value: '$totalBatches',
            color: DesertBrewColors.info,
          ),
          _KpiChip(
            label: 'Valor Total',
            value: fmt.format(totalValue),
            color: DesertBrewColors.primary,
          ),
          _KpiChip(
            label: 'Stock Bajo',
            value: '$lowStockItems',
            color:
                lowStockItems > 0
                    ? DesertBrewColors.warning
                    : DesertBrewColors.success,
          ),
        ],
      ),
    );
  }
}

class _KpiChip extends StatelessWidget {
  const _KpiChip({
    required this.label,
    required this.value,
    required this.color,
  });
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: DesertBrewColors.textHint,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

// ── Category Filter ────────────────────────────────────────────────────────

class _CategoryFilter extends StatelessWidget {
  const _CategoryFilter({this.selected});
  final String? selected;

  static const _categories = [
    ('MALT', '🌾 Malta'),
    ('HOPS', '🌿 Lúpulos'),
    ('YEAST', '🧫 Levadura'),
    ('BOTTLE', '🍾 Botellas'),
    ('CAP', '🧢 Tapas'),
    ('CHEMICAL', '⚗️ Químicos'),
    ('LABEL', '🏷 Etiquetas'),
    ('OTHER', '📦 Otros'),
  ];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        children: [
          _FilterChip(
            label: 'Todos',
            isSelected: selected == null,
            onTap: () => context.read<StockBloc>().add(StockLoadRequested()),
          ),
          ..._categories.map(
            (c) => _FilterChip(
              label: c.$2,
              isSelected: selected == c.$1,
              onTap:
                  () => context.read<StockBloc>().add(
                    StockLoadRequested(category: c.$1),
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label, style: const TextStyle(fontSize: 12)),
        selected: isSelected,
        onSelected: (_) => onTap(),
        selectedColor: DesertBrewColors.primary.withValues(alpha: 0.2),
        checkmarkColor: DesertBrewColors.primary,
      ),
    );
  }
}

class _ListModeToggle extends StatelessWidget {
  const _ListModeToggle({
    required this.selectedMode,
    required this.batchesCount,
    required this.suppliesCount,
    required this.onModeChanged,
  });

  final _StockListViewMode selectedMode;
  final int batchesCount;
  final int suppliesCount;
  final ValueChanged<_StockListViewMode> onModeChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 6),
      child: Container(
        decoration: BoxDecoration(
          color: DesertBrewColors.surface,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Expanded(
              child: _ModeButton(
                label: 'Lotes ($batchesCount)',
                selected: selectedMode == _StockListViewMode.batches,
                onTap: () => onModeChanged(_StockListViewMode.batches),
              ),
            ),
            Expanded(
              child: _ModeButton(
                label: 'Insumos ($suppliesCount)',
                selected: selectedMode == _StockListViewMode.supplies,
                onTap: () => onModeChanged(_StockListViewMode.supplies),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  const _ModeButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      curve: Curves.easeOut,
      margin: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color:
            selected
                ? DesertBrewColors.primary.withValues(alpha: 0.18)
                : Colors.transparent,
        borderRadius: BorderRadius.circular(10),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 9),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color:
                    selected
                        ? DesertBrewColors.primary
                        : DesertBrewColors.textSecondary,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Stock Batch Tile ───────────────────────────────────────────────────────

class _StockBatchTile extends StatelessWidget {
  const _StockBatchTile({required this.batch});
  final StockBatch batch;

  @override
  Widget build(BuildContext context) {
    final pct = batch.remainingPercent;
    final barColor =
        pct < 20
            ? DesertBrewColors.error
            : pct < 50
            ? DesertBrewColors.warning
            : DesertBrewColors.success;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    batch.ingredientName,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                ),
                if (batch.isLow)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: DesertBrewColors.warning.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      '⚠ Bajo',
                      style: TextStyle(
                        color: DesertBrewColors.warning,
                        fontSize: 11,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            // Progress bar
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: pct / 100,
                backgroundColor: DesertBrewColors.surfaceVariant,
                valueColor: AlwaysStoppedAnimation<Color>(barColor),
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${batch.remainingQuantity.toStringAsFixed(1)} / '
                  '${batch.quantity.toStringAsFixed(1)} ${batch.unit}',
                  style: const TextStyle(
                    color: DesertBrewColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
                Text(
                  '\$${batch.unitCost.toStringAsFixed(2)}/u',
                  style: const TextStyle(
                    color: DesertBrewColors.primary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            if (batch.supplierName != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  '📦 ${batch.supplierName}',
                  style: const TextStyle(
                    color: DesertBrewColors.textHint,
                    fontSize: 11,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _StockSupplyItem {
  const _StockSupplyItem({
    required this.sku,
    required this.category,
    required this.unit,
    required this.totalQuantity,
    required this.remainingQuantity,
    required this.remainingValue,
    required this.batchesCount,
    required this.lowStock,
    this.mainSupplier,
  });

  final String sku;
  final String category;
  final String unit;
  final double totalQuantity;
  final double remainingQuantity;
  final double remainingValue;
  final int batchesCount;
  final bool lowStock;
  final String? mainSupplier;

  double get remainingPercent =>
      totalQuantity <= 0 ? 0 : (remainingQuantity / totalQuantity) * 100;

  static List<_StockSupplyItem> fromBatches(List<StockBatch> batches) {
    final grouped = <String, _StockSupplyAccumulator>{};

    for (final batch in batches) {
      final key = '${batch.ingredientName}|${batch.category}|${batch.unit}';
      final current = grouped[key];
      if (current == null) {
        grouped[key] = _StockSupplyAccumulator(
          sku: batch.ingredientName,
          category: batch.category,
          unit: batch.unit,
          totalQuantity: batch.quantity,
          remainingQuantity: batch.remainingQuantity,
          remainingValue: batch.remainingQuantity * batch.unitCost,
          batchesCount: 1,
          lowStock: batch.isLow,
          mainSupplier: batch.supplierName,
        );
      } else {
        grouped[key] = current.copyWith(
          totalQuantity: current.totalQuantity + batch.quantity,
          remainingQuantity:
              current.remainingQuantity + batch.remainingQuantity,
          remainingValue:
              current.remainingValue +
              (batch.remainingQuantity * batch.unitCost),
          batchesCount: current.batchesCount + 1,
          lowStock: current.lowStock || batch.isLow,
          mainSupplier: current.mainSupplier ?? batch.supplierName,
        );
      }
    }

    final items =
        grouped.values
            .map(
              (item) => _StockSupplyItem(
                sku: item.sku,
                category: item.category,
                unit: item.unit,
                totalQuantity: item.totalQuantity,
                remainingQuantity: item.remainingQuantity,
                remainingValue: item.remainingValue,
                batchesCount: item.batchesCount,
                lowStock:
                    item.lowStock ||
                    (item.totalQuantity > 0 &&
                        ((item.remainingQuantity / item.totalQuantity) * 100 <
                            20)),
                mainSupplier: item.mainSupplier,
              ),
            )
            .toList()
          ..sort((a, b) => a.sku.toLowerCase().compareTo(b.sku.toLowerCase()));

    return items;
  }
}

class _StockSupplyAccumulator {
  const _StockSupplyAccumulator({
    required this.sku,
    required this.category,
    required this.unit,
    required this.totalQuantity,
    required this.remainingQuantity,
    required this.remainingValue,
    required this.batchesCount,
    required this.lowStock,
    this.mainSupplier,
  });

  final String sku;
  final String category;
  final String unit;
  final double totalQuantity;
  final double remainingQuantity;
  final double remainingValue;
  final int batchesCount;
  final bool lowStock;
  final String? mainSupplier;

  _StockSupplyAccumulator copyWith({
    double? totalQuantity,
    double? remainingQuantity,
    double? remainingValue,
    int? batchesCount,
    bool? lowStock,
    String? mainSupplier,
  }) {
    return _StockSupplyAccumulator(
      sku: sku,
      category: category,
      unit: unit,
      totalQuantity: totalQuantity ?? this.totalQuantity,
      remainingQuantity: remainingQuantity ?? this.remainingQuantity,
      remainingValue: remainingValue ?? this.remainingValue,
      batchesCount: batchesCount ?? this.batchesCount,
      lowStock: lowStock ?? this.lowStock,
      mainSupplier: mainSupplier ?? this.mainSupplier,
    );
  }
}

class _StockSupplyTile extends StatelessWidget {
  const _StockSupplyTile({required this.item});

  final _StockSupplyItem item;

  @override
  Widget build(BuildContext context) {
    final pct = item.remainingPercent;
    final barColor =
        pct < 20
            ? DesertBrewColors.error
            : pct < 50
            ? DesertBrewColors.warning
            : DesertBrewColors.success;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.sku,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${item.category} · ${item.batchesCount} lote(s)',
                        style: const TextStyle(
                          color: DesertBrewColors.textHint,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                if (item.lowStock)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: DesertBrewColors.warning.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      '⚠ Bajo',
                      style: TextStyle(
                        color: DesertBrewColors.warning,
                        fontSize: 11,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: pct / 100,
                backgroundColor: DesertBrewColors.surfaceVariant,
                valueColor: AlwaysStoppedAnimation<Color>(barColor),
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${item.remainingQuantity.toStringAsFixed(1)} / '
                  '${item.totalQuantity.toStringAsFixed(1)} ${item.unit}',
                  style: const TextStyle(
                    color: DesertBrewColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
                Text(
                  '\$${item.remainingValue.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: DesertBrewColors.primary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            if (item.mainSupplier != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  '📦 ${item.mainSupplier}',
                  style: const TextStyle(
                    color: DesertBrewColors.textHint,
                    fontSize: 11,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ── Error & Empty ──────────────────────────────────────────────────────────

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.wifi_off_rounded,
            size: 64,
            color: DesertBrewColors.error,
          ),
          const SizedBox(height: 16),
          const Text(
            'No se pudo conectar al backend',
            style: TextStyle(color: DesertBrewColors.textSecondary),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            style: const TextStyle(
              color: DesertBrewColors.textHint,
              fontSize: 11,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed:
                () => context.read<StockBloc>().add(StockRefreshRequested()),
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.viewMode});

  final _StockListViewMode viewMode;

  @override
  Widget build(BuildContext context) {
    final isSupplyView = viewMode == _StockListViewMode.supplies;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.inventory_2_rounded,
            size: 64,
            color: DesertBrewColors.textHint,
          ),
          const SizedBox(height: 16),
          Text(
            isSupplyView ? 'Sin insumos para mostrar' : 'Sin stock registrado',
            style: const TextStyle(color: DesertBrewColors.textSecondary),
          ),
          const SizedBox(height: 8),
          Text(
            isSupplyView
                ? 'Cambia filtros o recibe stock para ver insumos'
                : 'Usa el botón + para recibir materia prima',
            style: const TextStyle(
              color: DesertBrewColors.textHint,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
