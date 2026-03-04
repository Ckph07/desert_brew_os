import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/inventory_remote_datasource.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/finished_product.dart';
import '../bloc/finished_product/finished_product_bloc.dart';

class FinishedProductsPage extends StatefulWidget {
  const FinishedProductsPage({super.key});

  @override
  State<FinishedProductsPage> createState() => _FinishedProductsPageState();
}

class _FinishedProductsPageState extends State<FinishedProductsPage> {
  String? _typeFilter;

  static const _typeOptions = [null, 'OWN_PRODUCTION', 'COMMERCIAL', 'GUEST_CRAFT', 'MERCHANDISE'];
  static const _typeLabels = ['Todos', 'Prod. Propia', 'Comercial', 'Guest Craft', 'Merchandising'];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => FinishedProductBloc(
        InventoryRepositoryImpl(InventoryRemoteDataSource()),
      )..add(FinishedProductLoadRequested(productTypeFilter: _typeFilter)),
      child: Builder(builder: (ctx) => _buildBody(ctx)),
    );
  }

  Widget _buildBody(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Producto Terminado'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => context
                .read<FinishedProductBloc>()
                .add(FinishedProductLoadRequested(productTypeFilter: _typeFilter)),
          ),
        ],
      ),
      body: BlocBuilder<FinishedProductBloc, FinishedProductState>(
        builder: (context, state) {
          if (state is FinishedProductLoading || state is FinishedProductInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is FinishedProductError) {
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
                  ElevatedButton.icon(
                    onPressed: () => context
                        .read<FinishedProductBloc>()
                        .add(FinishedProductLoadRequested()),
                    icon: const Icon(Icons.refresh_rounded),
                    label: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }
          if (state is FinishedProductLoaded) {
            return _LoadedBody(
              state: state,
              typeFilter: _typeFilter,
              typeOptions: _typeOptions,
              typeLabels: _typeLabels,
              onFilterChanged: (f) {
                setState(() => _typeFilter = f);
                context
                    .read<FinishedProductBloc>()
                    .add(FinishedProductLoadRequested(productTypeFilter: f));
              },
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}

class _LoadedBody extends StatelessWidget {
  const _LoadedBody({
    required this.state,
    required this.typeFilter,
    required this.typeOptions,
    required this.typeLabels,
    required this.onFilterChanged,
  });

  final FinishedProductLoaded state;
  final String? typeFilter;
  final List<String?> typeOptions;
  final List<String> typeLabels;
  final void Function(String?) onFilterChanged;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    final totalItems = state.products.fold(0.0, (s, p) => s + p.quantity);
    final totalValue = state.products
        .fold(0.0, (s, p) => s + (p.totalCost ?? p.value));
    final expiringSoon = state.products.where((p) => p.isExpiringSoon).length;

    return CustomScrollView(
      slivers: [
        // ── Cold Room Status Bar ─────────────────────────────────
        SliverToBoxAdapter(
          child: state.coldRooms.isEmpty
              ? const SizedBox.shrink()
              : Container(
                  height: 56,
                  margin: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: DesertBrewColors.surface,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: state.coldRooms.map((room) {
                      final ok = room.isWithinRange;
                      final color = room.alertActive
                          ? DesertBrewColors.error
                          : ok
                              ? DesertBrewColors.success
                              : DesertBrewColors.warning;
                      return Expanded(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.thermostat_rounded,
                                color: color, size: 14),
                            Text(
                              '${room.currentTemp.toStringAsFixed(1)}°C',
                              style: TextStyle(
                                  color: color,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12),
                            ),
                            Text(room.id,
                                style: const TextStyle(
                                    color: DesertBrewColors.textHint,
                                    fontSize: 9),
                                overflow: TextOverflow.ellipsis),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
        ),

        // ── KPI Bar ───────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 12),
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: DesertBrewColors.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                _KpiCell('${totalItems.toStringAsFixed(0)}', 'Unidades / L',
                    DesertBrewColors.primary),
                _KpiCell(currency.format(totalValue), 'Valor Total',
                    DesertBrewColors.success),
                _KpiCell('$expiringSoon', 'Vence en 7d',
                    expiringSoon > 0 ? DesertBrewColors.error : DesertBrewColors.textHint),
              ],
            ),
          ),
        ),

        // ── Type Filter Chips ─────────────────────────────────────
        SliverToBoxAdapter(
          child: SizedBox(
            height: 44,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              itemCount: typeOptions.length,
              itemBuilder: (_, i) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  label: Text(typeLabels[i],
                      style: const TextStyle(fontSize: 11)),
                  selected: typeFilter == typeOptions[i],
                  onSelected: (_) => onFilterChanged(typeOptions[i]),
                  selectedColor:
                      DesertBrewColors.primary.withValues(alpha: 0.2),
                ),
              ),
            ),
          ),
        ),

        // ── Product List ──────────────────────────────────────────
        state.products.isEmpty
            ? SliverFillRemaining(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.inventory_2_outlined,
                          size: 56, color: DesertBrewColors.textHint),
                      SizedBox(height: 12),
                      Text('Sin productos en cámara',
                          style: TextStyle(
                              color: DesertBrewColors.textSecondary)),
                    ],
                  ),
                ),
              )
            : SliverPadding(
                padding: const EdgeInsets.fromLTRB(12, 4, 12, 20),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (_, i) => _ProductTile(product: state.products[i]),
                    childCount: state.products.length,
                  ),
                ),
              ),
      ],
    );
  }
}

class _ProductTile extends StatelessWidget {
  const _ProductTile({required this.product});
  final FinishedProduct product;

  Color get _statusColor {
    switch (product.availabilityStatus) {
      case AvailabilityStatus.available:
        return DesertBrewColors.success;
      case AvailabilityStatus.reserved:
        return DesertBrewColors.warning;
      case AvailabilityStatus.sold:
        return DesertBrewColors.primary;
      case AvailabilityStatus.expired:
        return DesertBrewColors.error;
      case AvailabilityStatus.damaged:
        return DesertBrewColors.error;
    }
  }

  Color get _typeColor {
    switch (product.productType) {
      case ProductType.ownProduction:
        return DesertBrewColors.primary;
      case ProductType.commercial:
        return DesertBrewColors.accent;
      case ProductType.guestCraft:
        return const Color(0xFF8B5CF6);
      case ProductType.merchandise:
        return DesertBrewColors.warning;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final fmt = DateFormat('dd/MM/yy');
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: product.isExpiringSoon
              ? DesertBrewColors.error.withValues(alpha: 0.5)
              : _typeColor.withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        children: [
          // Type badge
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: _typeColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                product.category.split('_').first,
                style: TextStyle(
                    color: _typeColor,
                    fontSize: 9,
                    fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(product.productName,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 13),
                          overflow: TextOverflow.ellipsis),
                    ),
                    if (product.isExpiringSoon)
                      const Icon(Icons.warning_amber_rounded,
                          color: DesertBrewColors.error, size: 14),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  '${product.sku} · ${product.coldRoomId}${product.shelfPosition != null ? ' [${product.shelfPosition}]' : ''}',
                  style: const TextStyle(
                      color: DesertBrewColors.textHint, fontSize: 11),
                ),
                if (product.bestBefore != null)
                  Text('Vence: ${fmt.format(product.bestBefore!)}',
                      style: TextStyle(
                          color: product.isExpiringSoon
                              ? DesertBrewColors.error
                              : DesertBrewColors.textHint,
                          fontSize: 10)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: _statusColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  product.availabilityStatus.displayName,
                  style: TextStyle(
                      color: _statusColor,
                      fontSize: 9,
                      fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${product.quantity.toStringAsFixed(product.quantity % 1 == 0 ? 0 : 1)} ${product.unitMeasure}',
                style: const TextStyle(
                    color: DesertBrewColors.primary,
                    fontWeight: FontWeight.bold,
                    fontSize: 12),
              ),
              if (product.unitCost != null)
                Text(
                  currency.format(product.unitCost),
                  style: const TextStyle(
                      color: DesertBrewColors.textHint, fontSize: 10),
                ),
            ],
          ),
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
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(value,
              style: TextStyle(
                  color: color, fontWeight: FontWeight.bold, fontSize: 13),
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
}
