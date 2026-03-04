import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/sales_remote_datasource.dart';
import '../../data/repositories/sales_repository_impl.dart';
import '../../domain/entities/product.dart';
import '../bloc/product/product_bloc.dart';

class ProductCatalogPage extends StatelessWidget {
  const ProductCatalogPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              ProductBloc(SalesRepositoryImpl(SalesRemoteDataSource()))
                ..add(ProductLoadRequested()),
      child: const _ProductCatalogView(),
    );
  }
}

class _ProductCatalogView extends StatelessWidget {
  const _ProductCatalogView();

  static const _categories = [
    (null, '🍺 Todos'),
    ('BEER_LITER', '🍺 Litros'),
    ('BEER_CAN', '🥫 Lata'),
    ('MERCH', '👕 Merch'),
    ('PACKAGING', '📦 Empaque'),
    ('OTHER', '📋 Otros'),
  ];
  static const _originTypes = ['HOUSE', 'GUEST', 'COMMERCIAL'];
  static const _units = ['LITROS', 'L', 'ML', 'UNITS', 'KEGS'];

  @override
  Widget build(BuildContext context) {
    final repo = SalesRepositoryImpl(SalesRemoteDataSource());
    return Scaffold(
      appBar: AppBar(
        title: const Text('Catálogo de Productos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.receipt_long_rounded),
            tooltip: 'Ver notas',
            onPressed: () => context.push('/sales/notes'),
          ),
          IconButton(
            icon: const Icon(Icons.people_alt_rounded),
            tooltip: 'Ver clientes',
            onPressed: () => context.push('/sales/clients'),
          ),
          IconButton(
            icon: const Icon(Icons.bar_chart_rounded),
            tooltip: 'Reporte de Márgenes',
            onPressed:
                () => context.read<ProductBloc>().add(MarginReportRequested()),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () => context.read<ProductBloc>().add(ProductLoadRequested()),
          ),
        ],
      ),
      body: Column(
        children: [
          // Category filters
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              children:
                  _categories.map((c) {
                    return BlocBuilder<ProductBloc, ProductState>(
                      builder: (context, state) {
                        final selected =
                            state is ProductLoaded
                                ? state.filterCategory
                                : null;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(
                              c.$2,
                              style: const TextStyle(fontSize: 12),
                            ),
                            selected: selected == c.$1,
                            onSelected:
                                (_) => context.read<ProductBloc>().add(
                                  ProductLoadRequested(category: c.$1),
                                ),
                            selectedColor: DesertBrewColors.primary.withValues(
                              alpha: 0.2,
                            ),
                            checkmarkColor: DesertBrewColors.primary,
                          ),
                        );
                      },
                    );
                  }).toList(),
            ),
          ),
          Expanded(
            child: BlocBuilder<ProductBloc, ProductState>(
              builder: (context, state) {
                if (state is ProductLoading || state is ProductInitial) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is ProductError) {
                  return Center(
                    child: Text(
                      state.message,
                      style: const TextStyle(color: DesertBrewColors.textHint),
                    ),
                  );
                }
                if (state is MarginReportLoaded) {
                  return _MarginReportView(state: state);
                }
                if (state is ProductLoaded) {
                  if (state.products.isEmpty) {
                    return const Center(
                      child: Text(
                        'Sin productos',
                        style: TextStyle(color: DesertBrewColors.textSecondary),
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.all(8),
                    itemCount: state.products.length,
                    itemBuilder:
                        (_, i) => _ProductTile(
                          product: state.products[i],
                          onEdit:
                              () => _editProduct(
                                context,
                                repo,
                                state.products[i],
                              ),
                          onDeactivate:
                              () => _deactivateProduct(
                                context,
                                repo,
                                state.products[i],
                              ),
                        ),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _createProduct(context, repo),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo Producto'),
      ),
    );
  }

  Future<void> _createProduct(
    BuildContext context,
    SalesRepositoryImpl repo,
  ) async {
    final payload = await _showProductFormDialog(context);
    if (payload == null || !context.mounted) return;
    try {
      await repo.createProduct(payload);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Producto creado'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
      _reloadCurrentFilter(context);
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error creando producto: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _editProduct(
    BuildContext context,
    SalesRepositoryImpl repo,
    Product product,
  ) async {
    final payload = await _showProductFormDialog(context, initial: product);
    if (payload == null || !context.mounted) return;
    try {
      await repo.updateProduct(product.id, payload);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Producto actualizado'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
      _reloadCurrentFilter(context);
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error actualizando producto: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _deactivateProduct(
    BuildContext context,
    SalesRepositoryImpl repo,
    Product product,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Desactivar producto'),
            content: Text(
              'Se desactivará ${product.productName} (${product.sku}).',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                style: FilledButton.styleFrom(
                  backgroundColor: DesertBrewColors.warning,
                ),
                child: const Text('Desactivar'),
              ),
            ],
          ),
    );
    if (confirmed != true || !context.mounted) return;

    try {
      await repo.deleteProduct(product.id);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Producto desactivado'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
      _reloadCurrentFilter(context);
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error desactivando producto: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  void _reloadCurrentFilter(BuildContext context) {
    final state = context.read<ProductBloc>().state;
    final selectedCategory =
        state is ProductLoaded ? state.filterCategory : null;
    context.read<ProductBloc>().add(
      ProductLoadRequested(category: selectedCategory),
    );
  }

  Future<Map<String, dynamic>?> _showProductFormDialog(
    BuildContext context, {
    Product? initial,
  }) async {
    final formKey = GlobalKey<FormState>();
    final skuCtrl = TextEditingController(text: initial?.sku ?? '');
    final nameCtrl = TextEditingController(text: initial?.productName ?? '');
    final descCtrl = TextEditingController(text: initial?.description ?? '');
    final styleCtrl = TextEditingController(text: initial?.style ?? '');
    final volumeCtrl = TextEditingController(
      text: initial?.volumeMl?.toString() ?? '',
    );
    final abvCtrl = TextEditingController(
      text: initial?.abv?.toStringAsFixed(2) ?? '',
    );
    final ibuCtrl = TextEditingController(text: initial?.ibu?.toString() ?? '');
    final fixedPriceCtrl = TextEditingController(
      text: initial?.fixedPrice?.toStringAsFixed(2) ?? '',
    );
    final theoreticalCtrl = TextEditingController(
      text: initial?.theoreticalPrice?.toStringAsFixed(2) ?? '',
    );
    final costCtrl = TextEditingController(
      text: initial?.costPerUnit?.toStringAsFixed(2) ?? '',
    );
    final taproomCtrl = TextEditingController(
      text: initial?.priceTaproom?.toStringAsFixed(2) ?? '',
    );
    final distributorCtrl = TextEditingController(
      text: initial?.priceDistributor?.toStringAsFixed(2) ?? '',
    );
    final onPremCtrl = TextEditingController(
      text: initial?.priceOnPremise?.toStringAsFixed(2) ?? '',
    );
    final offPremCtrl = TextEditingController(
      text: initial?.priceOffPremise?.toStringAsFixed(2) ?? '',
    );
    final ecommerceCtrl = TextEditingController(
      text: initial?.priceEcommerce?.toStringAsFixed(2) ?? '',
    );
    final notesCtrl = TextEditingController(text: initial?.notes ?? '');

    var category = initial?.category ?? 'BEER_LITER';
    var originType = initial?.originType ?? 'HOUSE';
    var unitMeasure = initial?.unitMeasure ?? 'LITROS';
    Map<String, dynamic>? result;

    try {
      final saved = await showDialog<bool>(
        context: context,
        builder:
            (ctx) => StatefulBuilder(
              builder:
                  (ctx, setSt) => AlertDialog(
                    title: Text(
                      initial == null
                          ? 'Nuevo Producto'
                          : 'Editar ${initial.sku}',
                    ),
                    content: SizedBox(
                      width: 560,
                      child: Form(
                        key: formKey,
                        child: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              TextFormField(
                                controller: skuCtrl,
                                enabled: initial == null,
                                decoration: const InputDecoration(
                                  labelText: 'SKU *',
                                ),
                                validator: (v) {
                                  if (initial != null) return null;
                                  return (v == null || v.trim().isEmpty)
                                      ? 'SKU requerido'
                                      : null;
                                },
                              ),
                              const SizedBox(height: 8),
                              TextFormField(
                                controller: nameCtrl,
                                decoration: const InputDecoration(
                                  labelText: 'Nombre *',
                                ),
                                validator:
                                    (v) =>
                                        (v == null || v.trim().isEmpty)
                                            ? 'Requerido'
                                            : null,
                              ),
                              const SizedBox(height: 8),
                              DropdownButtonFormField<String>(
                                value: category,
                                decoration: const InputDecoration(
                                  labelText: 'Categoría *',
                                ),
                                items:
                                    const [
                                          'BEER_LITER',
                                          'BEER_CAN',
                                          'MERCH',
                                          'PACKAGING',
                                          'OTHER',
                                        ]
                                        .map(
                                          (v) => DropdownMenuItem(
                                            value: v,
                                            child: Text(v),
                                          ),
                                        )
                                        .toList(),
                                onChanged:
                                    (v) =>
                                        setSt(() => category = v ?? category),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: DropdownButtonFormField<String>(
                                      value: originType,
                                      decoration: const InputDecoration(
                                        labelText: 'Origen',
                                      ),
                                      items:
                                          _originTypes
                                              .map(
                                                (v) => DropdownMenuItem(
                                                  value: v,
                                                  child: Text(v),
                                                ),
                                              )
                                              .toList(),
                                      onChanged:
                                          (v) => setSt(
                                            () => originType = v ?? originType,
                                          ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: DropdownButtonFormField<String>(
                                      value: unitMeasure,
                                      decoration: const InputDecoration(
                                        labelText: 'Unidad',
                                      ),
                                      items:
                                          _units
                                              .map(
                                                (v) => DropdownMenuItem(
                                                  value: v,
                                                  child: Text(v),
                                                ),
                                              )
                                              .toList(),
                                      onChanged:
                                          (v) => setSt(
                                            () =>
                                                unitMeasure = v ?? unitMeasure,
                                          ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              TextFormField(
                                controller: descCtrl,
                                decoration: const InputDecoration(
                                  labelText: 'Descripción',
                                ),
                                maxLines: 2,
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      controller: styleCtrl,
                                      decoration: const InputDecoration(
                                        labelText: 'Estilo',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: TextFormField(
                                      controller: volumeCtrl,
                                      keyboardType: TextInputType.number,
                                      decoration: const InputDecoration(
                                        labelText: 'Volumen ml',
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      controller: abvCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'ABV',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: TextFormField(
                                      controller: ibuCtrl,
                                      keyboardType: TextInputType.number,
                                      decoration: const InputDecoration(
                                        labelText: 'IBU',
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const Divider(height: 20),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      controller: fixedPriceCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'Precio fijo',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: TextFormField(
                                      controller: theoreticalCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'Precio teórico',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: TextFormField(
                                      controller: costCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'Costo/u',
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      controller: taproomCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'Taproom',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: TextFormField(
                                      controller: distributorCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'Distribuidor',
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      controller: onPremCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'On-Premise',
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: TextFormField(
                                      controller: offPremCtrl,
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText: 'Off-Premise',
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              TextFormField(
                                controller: ecommerceCtrl,
                                keyboardType:
                                    const TextInputType.numberWithOptions(
                                      decimal: true,
                                    ),
                                decoration: const InputDecoration(
                                  labelText: 'Ecommerce',
                                ),
                              ),
                              const SizedBox(height: 8),
                              TextFormField(
                                controller: notesCtrl,
                                decoration: const InputDecoration(
                                  labelText: 'Notas',
                                ),
                                maxLines: 2,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(ctx).pop(false),
                        child: const Text('Cancelar'),
                      ),
                      FilledButton(
                        onPressed: () {
                          if (!(formKey.currentState?.validate() ?? false)) {
                            return;
                          }

                          result = {
                            if (initial == null) 'sku': skuCtrl.text.trim(),
                            'product_name': nameCtrl.text.trim(),
                            'description':
                                descCtrl.text.trim().isEmpty
                                    ? null
                                    : descCtrl.text.trim(),
                            'style':
                                styleCtrl.text.trim().isEmpty
                                    ? null
                                    : styleCtrl.text.trim(),
                            'category': category,
                            'origin_type': originType,
                            'unit_measure': unitMeasure,
                            'volume_ml': int.tryParse(volumeCtrl.text.trim()),
                            'abv': _parseNullableDouble(abvCtrl.text),
                            'ibu': int.tryParse(ibuCtrl.text.trim()),
                            'fixed_price': _parseNullableDouble(
                              fixedPriceCtrl.text,
                            ),
                            'theoretical_price': _parseNullableDouble(
                              theoreticalCtrl.text,
                            ),
                            'cost_per_unit': _parseNullableDouble(
                              costCtrl.text,
                            ),
                            'price_taproom': _parseNullableDouble(
                              taproomCtrl.text,
                            ),
                            'price_distributor': _parseNullableDouble(
                              distributorCtrl.text,
                            ),
                            'price_on_premise': _parseNullableDouble(
                              onPremCtrl.text,
                            ),
                            'price_off_premise': _parseNullableDouble(
                              offPremCtrl.text,
                            ),
                            'price_ecommerce': _parseNullableDouble(
                              ecommerceCtrl.text,
                            ),
                            'notes':
                                notesCtrl.text.trim().isEmpty
                                    ? null
                                    : notesCtrl.text.trim(),
                          };
                          Navigator.of(ctx).pop(true);
                        },
                        child: const Text('Guardar'),
                      ),
                    ],
                  ),
            ),
      );
      return saved == true ? result : null;
    } finally {
      skuCtrl.dispose();
      nameCtrl.dispose();
      descCtrl.dispose();
      styleCtrl.dispose();
      volumeCtrl.dispose();
      abvCtrl.dispose();
      ibuCtrl.dispose();
      fixedPriceCtrl.dispose();
      theoreticalCtrl.dispose();
      costCtrl.dispose();
      taproomCtrl.dispose();
      distributorCtrl.dispose();
      onPremCtrl.dispose();
      offPremCtrl.dispose();
      ecommerceCtrl.dispose();
      notesCtrl.dispose();
    }
  }

  static double? _parseNullableDouble(String value) {
    final clean = value.trim().replaceAll(',', '.');
    if (clean.isEmpty) return null;
    return double.tryParse(clean);
  }
}

// ── Product Tile ───────────────────────────────────────────────────────────

enum _ProductAction { edit, deactivate }

class _ProductTile extends StatelessWidget {
  const _ProductTile({
    required this.product,
    required this.onEdit,
    required this.onDeactivate,
  });
  final Product product;
  final VoidCallback onEdit;
  final VoidCallback onDeactivate;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor:
              product.isHouse
                  ? DesertBrewColors.primary.withValues(alpha: 0.15)
                  : DesertBrewColors.accent.withValues(alpha: 0.15),
          child: Text(
            product.isHouse ? '🏠' : '🍺',
            style: const TextStyle(fontSize: 16),
          ),
        ),
        title: Text(
          product.productName,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
        ),
        subtitle: Text(
          '${product.sku} · ${product.unitMeasure}'
          '${product.abv != null ? ' · ${product.abv!.toStringAsFixed(1)}% ABV' : ''}',
          style: const TextStyle(
            color: DesertBrewColors.textHint,
            fontSize: 11,
          ),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '\$${product.displayPrice.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: DesertBrewColors.primary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (product.fixedMarginPct != null)
                  Text(
                    '${product.fixedMarginPct!.toStringAsFixed(1)}% m.',
                    style: TextStyle(
                      color:
                          product.fixedMarginPct! >= 30
                              ? DesertBrewColors.success
                              : DesertBrewColors.warning,
                      fontSize: 10,
                    ),
                  ),
              ],
            ),
            PopupMenuButton<_ProductAction>(
              tooltip: 'Acciones',
              onSelected: (action) {
                switch (action) {
                  case _ProductAction.edit:
                    onEdit();
                    break;
                  case _ProductAction.deactivate:
                    onDeactivate();
                    break;
                }
              },
              itemBuilder:
                  (context) => const [
                    PopupMenuItem(
                      value: _ProductAction.edit,
                      child: ListTile(
                        dense: true,
                        leading: Icon(Icons.edit_rounded),
                        title: Text('Editar'),
                      ),
                    ),
                    PopupMenuItem(
                      value: _ProductAction.deactivate,
                      child: ListTile(
                        dense: true,
                        leading: Icon(Icons.block_rounded),
                        title: Text('Desactivar'),
                      ),
                    ),
                  ],
            ),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Column(
              children: [
                if (product.priceTaproom != null) ...[
                  const Divider(),
                  const Text(
                    'Precios por canal',
                    style: TextStyle(
                      color: DesertBrewColors.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  _PriceRow('Taproom', product.priceTaproom),
                  _PriceRow('Distribuidor', product.priceDistributor),
                  _PriceRow('On-Premise', product.priceOnPremise),
                  _PriceRow('Off-Premise', product.priceOffPremise),
                ],
                if (product.costPerUnit != null) ...[
                  const Divider(),
                  _PriceRow(
                    'Costo/u',
                    product.costPerUnit,
                    color: DesertBrewColors.error,
                  ),
                  _PriceRow(
                    'Precio Teórico',
                    product.theoreticalPrice,
                    color: DesertBrewColors.textSecondary,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PriceRow extends StatelessWidget {
  const _PriceRow(this.label, this.value, {this.color});
  final String label;
  final double? value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    if (value == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: DesertBrewColors.textHint,
              fontSize: 12,
            ),
          ),
          Text(
            '\$${value!.toStringAsFixed(2)}',
            style: TextStyle(
              color: color ?? DesertBrewColors.textSecondary,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Margin Report ──────────────────────────────────────────────────────────

class _MarginReportView extends StatelessWidget {
  const _MarginReportView({required this.state});
  final MarginReportLoaded state;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          color: DesertBrewColors.surface,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _Kpi(
                'Marg. Fijo Prom.',
                '${state.avgFixedMargin?.toStringAsFixed(1) ?? '—'}%',
                DesertBrewColors.primary,
              ),
              _Kpi(
                'Marg. Teórico Prom.',
                '${state.avgTheoreticalMargin?.toStringAsFixed(1) ?? '—'}%',
                DesertBrewColors.info,
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: state.items.length,
            itemBuilder: (_, i) {
              final item = state.items[i];
              final fixed = (item['fixed_margin_pct'] as num?)?.toDouble();
              return Card(
                margin: const EdgeInsets.only(bottom: 6),
                child: ListTile(
                  title: Text(
                    item['product_name'] as String,
                    style: const TextStyle(fontSize: 13),
                  ),
                  subtitle: Text(
                    item['sku'] as String,
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 11,
                    ),
                  ),
                  trailing:
                      fixed != null
                          ? Text(
                            '${fixed.toStringAsFixed(1)}%',
                            style: TextStyle(
                              color:
                                  fixed >= 30
                                      ? DesertBrewColors.success
                                      : DesertBrewColors.warning,
                              fontWeight: FontWeight.bold,
                            ),
                          )
                          : null,
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _Kpi extends StatelessWidget {
  const _Kpi(this.label, this.value, this.color);
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => Column(
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
        style: const TextStyle(color: DesertBrewColors.textHint, fontSize: 11),
      ),
    ],
  );
}
