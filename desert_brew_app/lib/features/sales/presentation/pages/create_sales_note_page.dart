import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/sales_remote_datasource.dart';
import '../../data/repositories/sales_repository_impl.dart';
import '../../domain/entities/product.dart';
import '../bloc/client/client_bloc.dart';
import '../bloc/product/product_bloc.dart';
import '../bloc/sales_note/sales_note_bloc.dart';

/// A mutable line item for the form (not the domain entity).
class _LineItem {
  _LineItem();
  final nameCtrl = TextEditingController();
  final qtyCtrl = TextEditingController();
  final priceCtrl = TextEditingController();
  int? productId;
  String? productSku;
  String unit = 'LITROS';
  double discount = 0;

  Map<String, dynamic> toPayload() => {
    if (productId != null) 'product_id': productId,
    if (productSku != null) 'sku': productSku,
    'product_name': nameCtrl.text.trim(),
    'unit_measure': unit,
    'quantity': double.tryParse(qtyCtrl.text) ?? 0,
    'unit_price': double.tryParse(priceCtrl.text) ?? 0,
    'discount_pct': discount,
    'ieps_rate': 0,
    'iva_rate': 0.16,
  };

  double get lineTotal {
    final qty = double.tryParse(qtyCtrl.text) ?? 0;
    final price = double.tryParse(priceCtrl.text) ?? 0;
    return qty * price * (1 - discount / 100);
  }

  void dispose() {
    nameCtrl.dispose();
    qtyCtrl.dispose();
    priceCtrl.dispose();
  }
}

class CreateSalesNotePage extends StatefulWidget {
  const CreateSalesNotePage({super.key});

  @override
  State<CreateSalesNotePage> createState() => _CreateSalesNotePageState();
}

class _CreateSalesNotePageState extends State<CreateSalesNotePage> {
  final _formKey = GlobalKey<FormState>();
  final _clientNameCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  final _createdByCtrl = TextEditingController();

  String _channel = 'B2B';
  String _paymentMethod = 'TRANSFERENCIA';
  bool _includeTaxes = false;
  int? _selectedClientId;
  final List<_LineItem> _items = [_LineItem()];

  static const _channels = ['B2B', 'B2C', 'TAPROOM', 'DISTRIBUTOR'];
  static const _payments = ['TRANSFERENCIA', 'EFECTIVO', 'TARJETA', 'CHEQUE'];
  static const _units = ['LITROS', 'L', 'ML', 'UNITS', 'UNIT', 'KEGS'];

  @override
  void dispose() {
    _clientNameCtrl.dispose();
    _notesCtrl.dispose();
    _createdByCtrl.dispose();
    for (final item in _items) {
      item.dispose();
    }
    super.dispose();
  }

  double get _grandTotal => _items.fold(0, (sum, item) => sum + item.lineTotal);

  @override
  Widget build(BuildContext context) {
    final repo = SalesRepositoryImpl(SalesRemoteDataSource());

    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => SalesNoteBloc(repo)),
        BlocProvider(
          create: (_) => ClientBloc(repo)..add(ClientLoadRequested()),
        ),
        BlocProvider(
          create: (_) => ProductBloc(repo)..add(ProductLoadRequested()),
        ),
      ],
      child: BlocListener<SalesNoteBloc, SalesNoteState>(
        listener: (context, state) {
          if (state is SalesNoteCreateSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('✓ Nota ${state.note.noteNumber} creada'),
                backgroundColor: DesertBrewColors.success,
              ),
            );
            context.pop();
          } else if (state is SalesNoteError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: DesertBrewColors.error,
              ),
            );
          }
        },
        child: Scaffold(
          appBar: AppBar(title: const Text('Nueva Nota de Venta')),
          body: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // ── Header ──────────────────────────────────────────
                _SectionHeader('📋 Datos Generales'),
                const SizedBox(height: 8),

                // Client selector
                BlocBuilder<ClientBloc, ClientState>(
                  builder: (context, state) {
                    final clients =
                        state is ClientLoaded ? state.clients : const [];
                    return DropdownButtonFormField<int?>(
                      value: _selectedClientId,
                      decoration: const InputDecoration(
                        labelText: 'Cliente',
                        prefixIcon: Icon(Icons.business_rounded),
                      ),
                      items: [
                        const DropdownMenuItem(
                          value: null,
                          child: Text('Sin cliente'),
                        ),
                        ...clients.map(
                          (c) => DropdownMenuItem(
                            value: c.id as int,
                            child: Text(c.businessName as String),
                          ),
                        ),
                      ],
                      onChanged: (v) {
                        setState(() => _selectedClientId = v);
                        if (v == null) return;
                        final client = clients.firstWhere((c) => c.id == v);
                        _clientNameCtrl.text = client.businessName;
                      },
                    );
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _clientNameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre en nota',
                    hintText: 'Nombre que aparece en el documento',
                    prefixIcon: Icon(Icons.person_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _channel,
                        decoration: const InputDecoration(labelText: 'Canal'),
                        items:
                            _channels
                                .map(
                                  (c) => DropdownMenuItem(
                                    value: c,
                                    child: Text(c),
                                  ),
                                )
                                .toList(),
                        onChanged: (v) => setState(() => _channel = v!),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _paymentMethod,
                        decoration: const InputDecoration(labelText: 'Pago'),
                        items:
                            _payments
                                .map(
                                  (p) => DropdownMenuItem(
                                    value: p,
                                    child: Text(p),
                                  ),
                                )
                                .toList(),
                        onChanged: (v) => setState(() => _paymentMethod = v!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  value: _includeTaxes,
                  onChanged: (v) => setState(() => _includeTaxes = v),
                  title: const Text('Incluir IEPS/IVA en la nota'),
                  subtitle: const Text(
                    'Actívalo si requiere desglose fiscal',
                    style: TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 11,
                    ),
                  ),
                  dense: true,
                ),
                const SizedBox(height: 16),

                // ── Items ────────────────────────────────────────────
                _SectionHeader('📦 Líneas de Producto'),
                const SizedBox(height: 8),
                BlocBuilder<ProductBloc, ProductState>(
                  builder: (context, state) {
                    final products =
                        state is ProductLoaded
                            ? state.products
                            : const <Product>[];
                    return Column(
                      children:
                          _items.asMap().entries.map((entry) {
                            final i = entry.key;
                            final item = entry.value;
                            return _LineItemCard(
                              index: i,
                              item: item,
                              units: _units,
                              products: products,
                              canDelete: _items.length > 1,
                              onDelete:
                                  () => setState(() {
                                    item.dispose();
                                    _items.removeAt(i);
                                  }),
                              onChanged: () => setState(() {}),
                            );
                          }).toList(),
                    );
                  },
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => setState(() => _items.add(_LineItem())),
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Agregar línea'),
                ),
                const SizedBox(height: 16),

                // ── Total ─────────────────────────────────────────────
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: DesertBrewColors.surface,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Total estimado',
                        style: TextStyle(color: DesertBrewColors.textSecondary),
                      ),
                      Text(
                        '\$${_grandTotal.toStringAsFixed(2)}',
                        style: const TextStyle(
                          color: DesertBrewColors.primary,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _notesCtrl,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Notas (opcional)',
                    prefixIcon: Icon(Icons.notes_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _createdByCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Creado por',
                    prefixIcon: Icon(Icons.person_pin_rounded),
                  ),
                ),
                const SizedBox(height: 24),

                // Submit
                BlocBuilder<SalesNoteBloc, SalesNoteState>(
                  builder: (context, state) {
                    final isSending = state is SalesNoteSubmitting;
                    return FilledButton.icon(
                      onPressed: isSending ? null : _submit,
                      icon:
                          isSending
                              ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                              : const Icon(Icons.send_rounded),
                      label: Text(
                        isSending
                            ? 'Guardando...'
                            : 'Crear Nota de Venta (Borrador)',
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final validItems =
        _items
            .where(
              (i) =>
                  i.productId != null &&
                  i.productSku != null &&
                  i.productSku!.trim().isNotEmpty &&
                  i.nameCtrl.text.trim().isNotEmpty &&
                  (double.tryParse(i.qtyCtrl.text) ?? 0) > 0 &&
                  (double.tryParse(i.priceCtrl.text) ?? 0) >= 0,
            )
            .toList();
    if (validItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Selecciona producto de catálogo y cantidad en cada línea',
          ),
          backgroundColor: DesertBrewColors.warning,
        ),
      );
      return;
    }
    context.read<SalesNoteBloc>().add(
      SalesNoteCreateSubmitted(
        items: validItems.map((i) => i.toPayload()).toList(),
        clientId: _selectedClientId,
        clientName:
            _clientNameCtrl.text.trim().isNotEmpty
                ? _clientNameCtrl.text.trim()
                : null,
        channel: _channel,
        paymentMethod: _paymentMethod,
        includeTaxes: _includeTaxes,
        notes:
            _notesCtrl.text.trim().isNotEmpty ? _notesCtrl.text.trim() : null,
        createdBy:
            _createdByCtrl.text.trim().isNotEmpty
                ? _createdByCtrl.text.trim()
                : null,
      ),
    );
  }
}

class _LineItemCard extends StatelessWidget {
  const _LineItemCard({
    required this.index,
    required this.item,
    required this.units,
    required this.products,
    required this.canDelete,
    required this.onDelete,
    required this.onChanged,
  });
  final int index;
  final _LineItem item;
  final List<String> units;
  final List<Product> products;
  final bool canDelete;
  final VoidCallback onDelete;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  'Línea ${index + 1}',
                  style: const TextStyle(
                    color: DesertBrewColors.textHint,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                if (canDelete)
                  IconButton(
                    icon: const Icon(
                      Icons.delete_rounded,
                      size: 18,
                      color: DesertBrewColors.error,
                    ),
                    onPressed: onDelete,
                    padding: EdgeInsets.zero,
                  ),
              ],
            ),
            DropdownButtonFormField<int>(
              value: item.productId,
              decoration: const InputDecoration(
                labelText: 'Producto del catálogo *',
                isDense: true,
              ),
              items:
                  products
                      .map(
                        (p) => DropdownMenuItem<int>(
                          value: p.id,
                          child: Text('${p.sku} · ${p.productName}'),
                        ),
                      )
                      .toList(),
              onChanged:
                  products.isEmpty
                      ? null
                      : (productId) {
                        if (productId == null) return;
                        final product = products.firstWhere(
                          (p) => p.id == productId,
                        );
                        item.productId = product.id;
                        item.productSku = product.sku;
                        item.nameCtrl.text = product.productName;
                        if ((double.tryParse(item.priceCtrl.text) ?? 0) <= 0 &&
                            product.displayPrice > 0) {
                          item.priceCtrl.text = product.displayPrice
                              .toStringAsFixed(2);
                        }
                        if (units.contains(product.unitMeasure.toUpperCase())) {
                          item.unit = product.unitMeasure.toUpperCase();
                        }
                        onChanged();
                      },
              validator:
                  (_) =>
                      item.productId == null ? 'Selecciona un producto' : null,
            ),
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                item.productSku ?? 'SKU pendiente',
                style: const TextStyle(
                  color: DesertBrewColors.textHint,
                  fontSize: 11,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: item.qtyCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    decoration: const InputDecoration(
                      labelText: 'Cantidad',
                      isDense: true,
                    ),
                    onChanged: (_) => onChanged(),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: item.priceCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    decoration: const InputDecoration(
                      labelText: 'Precio \$',
                      isDense: true,
                    ),
                    onChanged: (_) => onChanged(),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 2,
                  child: DropdownButtonFormField<String>(
                    value: item.unit,
                    isDense: true,
                    decoration: const InputDecoration(labelText: 'Unidad'),
                    items:
                        units
                            .map(
                              (u) => DropdownMenuItem(value: u, child: Text(u)),
                            )
                            .toList(),
                    onChanged: (v) {
                      item.unit = v!;
                      onChanged();
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Text(
                  'Subtotal: \$${item.lineTotal.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: DesertBrewColors.primary,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);
  final String title;

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        color: DesertBrewColors.primary,
        fontWeight: FontWeight.bold,
        fontSize: 13,
      ),
    );
  }
}
