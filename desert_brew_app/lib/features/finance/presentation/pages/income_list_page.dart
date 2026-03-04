import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/finance_remote_datasource.dart';
import '../../data/repositories/finance_repository_impl.dart';
import '../../domain/entities/income_entry.dart';
import '../bloc/income/income_bloc.dart';

class IncomeListPage extends StatefulWidget {
  const IncomeListPage({super.key});
  @override
  State<IncomeListPage> createState() => _IncomeListPageState();
}

class _IncomeListPageState extends State<IncomeListPage> {
  int _days = 30;
  String? _category;

  static const _dayOptions = [7, 30, 90, 365];
  static const _categories = <String?>[
    null,
    'beer_sales',
    'merch_sales',
    'food_sales',
    'event',
    'other',
  ];
  static const _catLabels = [
    'Todos',
    'Cerveza',
    'Merch',
    'Alimentos',
    'Eventos',
    'Otro',
  ];
  static const _incomeTypes = [
    'sales_note',
    'cash_sale',
    'b2b_invoice',
    'other',
  ];
  static const _paymentMethods = ['cash', 'card', 'transfer', 'check'];
  static const _profitCenters = ['taproom', 'distribution'];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              IncomeBloc(FinanceRepositoryImpl(FinanceRemoteDataSource()))
                ..add(IncomeLoadRequested(days: _days, category: _category)),
      child: Builder(builder: _buildBody),
    );
  }

  Widget _buildBody(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ingresos'),
        actions: [
          PopupMenuButton<int>(
            icon: const Icon(Icons.calendar_today_rounded),
            onSelected: (d) {
              setState(() => _days = d);
              context.read<IncomeBloc>().add(
                IncomeLoadRequested(days: d, category: _category),
              );
            },
            itemBuilder:
                (_) =>
                    _dayOptions
                        .map(
                          (d) => PopupMenuItem(
                            value: d,
                            child: Text('Últimos $d días'),
                          ),
                        )
                        .toList(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () => context.read<IncomeBloc>().add(
                  IncomeLoadRequested(days: _days, category: _category),
                ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openIncomeForm(context),
        child: const Icon(Icons.add_rounded),
      ),
      body: BlocConsumer<IncomeBloc, IncomeBlocState>(
        listener: (context, state) {
          if (state is IncomeActionSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: DesertBrewColors.success,
              ),
            );
          } else if (state is IncomeError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: DesertBrewColors.error,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is IncomeLoading || state is IncomeInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is IncomeLoaded) {
            return CustomScrollView(
              slivers: [
                // ── KPI Bar ─────────────────────────────────────────
                SliverToBoxAdapter(
                  child: Container(
                    margin: const EdgeInsets.all(12),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      color: DesertBrewColors.surface,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        _KpiCell(
                          currency.format(state.summary.totalIncome),
                          'Total Ingresos',
                          DesertBrewColors.success,
                        ),
                        _KpiCell(
                          '${state.summary.count}',
                          'Registros',
                          DesertBrewColors.primary,
                        ),
                        _KpiCell(
                          state.summary.byPaymentMethod.entries.isNotEmpty
                              ? currency.format(
                                state.summary.byPaymentMethod.values.reduce(
                                  (a, b) => a > b ? a : b,
                                ),
                              )
                              : '—',
                          'Mayor método',
                          DesertBrewColors.warning,
                        ),
                      ],
                    ),
                  ),
                ),

                // ── Category filter ──────────────────────────────────
                SliverToBoxAdapter(
                  child: SizedBox(
                    height: 42,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: _categories.length,
                      itemBuilder:
                          (_, i) => Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: FilterChip(
                              label: Text(
                                _catLabels[i],
                                style: const TextStyle(fontSize: 11),
                              ),
                              selected: _category == _categories[i],
                              onSelected: (_) {
                                setState(() => _category = _categories[i]);
                                context.read<IncomeBloc>().add(
                                  IncomeLoadRequested(
                                    days: _days,
                                    category: _categories[i],
                                  ),
                                );
                              },
                              selectedColor: DesertBrewColors.success
                                  .withValues(alpha: 0.2),
                            ),
                          ),
                    ),
                  ),
                ),

                // ── Category breakdown bar ───────────────────────────
                if (state.summary.byCategory.isNotEmpty)
                  SliverToBoxAdapter(
                    child: Container(
                      margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: DesertBrewColors.surface,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Por Categoría',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          const SizedBox(height: 8),
                          ...state.summary.byCategory.entries.map((e) {
                            final pct =
                                state.summary.totalIncome > 0
                                    ? e.value / state.summary.totalIncome
                                    : 0.0;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 6),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 80,
                                    child: Text(
                                      e.key,
                                      style: const TextStyle(
                                        color: DesertBrewColors.textHint,
                                        fontSize: 10,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  Expanded(
                                    child: ClipRRect(
                                      borderRadius: BorderRadius.circular(4),
                                      child: LinearProgressIndicator(
                                        value: pct,
                                        backgroundColor: DesertBrewColors
                                            .success
                                            .withValues(alpha: 0.1),
                                        valueColor:
                                            const AlwaysStoppedAnimation(
                                              DesertBrewColors.success,
                                            ),
                                        minHeight: 8,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    currency.format(e.value),
                                    style: const TextStyle(
                                      fontSize: 10,
                                      color: DesertBrewColors.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
                  ),

                // ── Income list ──────────────────────────────────────
                state.incomes.isEmpty
                    ? SliverFillRemaining(
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Icon(
                              Icons.trending_up_rounded,
                              size: 48,
                              color: DesertBrewColors.textHint,
                            ),
                            SizedBox(height: 12),
                            Text(
                              'Sin ingresos en el período',
                              style: TextStyle(
                                color: DesertBrewColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    )
                    : SliverPadding(
                      padding: const EdgeInsets.fromLTRB(12, 8, 12, 20),
                      sliver: SliverList(
                        delegate: SliverChildBuilderDelegate(
                          (_, i) => _IncomeTile(
                            income: state.incomes[i],
                            onEdit:
                                () => _openIncomeForm(
                                  context,
                                  existing: state.incomes[i],
                                ),
                            onDelete:
                                () => _confirmDeleteIncome(state.incomes[i]),
                          ),
                          childCount: state.incomes.length,
                        ),
                      ),
                    ),
              ],
            );
          }
          if (state is IncomeError) {
            return Center(
              child: Text(
                state.message,
                style: const TextStyle(color: DesertBrewColors.error),
              ),
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }

  Future<void> _openIncomeForm(
    BuildContext context, {
    IncomeEntry? existing,
  }) async {
    final descriptionCtrl = TextEditingController(
      text: existing?.description ?? '',
    );
    final amountCtrl = TextEditingController(
      text: existing != null ? existing.amount.toStringAsFixed(2) : '',
    );
    final refCtrl = TextEditingController(text: existing?.referenceId ?? '');
    final notesCtrl = TextEditingController(text: existing?.notes ?? '');
    final receivedByCtrl = TextEditingController(
      text: existing?.receivedBy ?? '',
    );

    var incomeType = existing?.incomeType ?? _incomeTypes.first;
    var category = existing?.category ?? 'beer_sales';
    var paymentMethod = existing?.paymentMethod ?? _paymentMethods.first;
    var profitCenter = existing?.profitCenter ?? _profitCenters.first;

    await showDialog<void>(
      context: context,
      builder:
          (ctx) => StatefulBuilder(
            builder:
                (ctx, setStateDialog) => AlertDialog(
                  title: Text(
                    existing == null ? 'Nuevo Ingreso' : 'Editar Ingreso',
                  ),
                  content: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        DropdownButtonFormField<String>(
                          value: incomeType,
                          decoration: const InputDecoration(labelText: 'Tipo'),
                          items:
                              _incomeTypes
                                  .map(
                                    (e) => DropdownMenuItem(
                                      value: e,
                                      child: Text(e),
                                    ),
                                  )
                                  .toList(),
                          onChanged:
                              (v) => setStateDialog(() => incomeType = v!),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          value: category,
                          decoration: const InputDecoration(
                            labelText: 'Categoria',
                          ),
                          items:
                              _categories
                                  .whereType<String>()
                                  .map(
                                    (e) => DropdownMenuItem(
                                      value: e,
                                      child: Text(e),
                                    ),
                                  )
                                  .toList(),
                          onChanged: (v) => setStateDialog(() => category = v!),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: descriptionCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Descripcion',
                          ),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: amountCtrl,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: const InputDecoration(labelText: 'Monto'),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          value: paymentMethod,
                          decoration: const InputDecoration(
                            labelText: 'Metodo de pago',
                          ),
                          items:
                              _paymentMethods
                                  .map(
                                    (e) => DropdownMenuItem(
                                      value: e,
                                      child: Text(e),
                                    ),
                                  )
                                  .toList(),
                          onChanged:
                              (v) => setStateDialog(() => paymentMethod = v!),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          value: profitCenter,
                          decoration: const InputDecoration(
                            labelText: 'Centro de utilidad',
                          ),
                          items:
                              _profitCenters
                                  .map(
                                    (e) => DropdownMenuItem(
                                      value: e,
                                      child: Text(e),
                                    ),
                                  )
                                  .toList(),
                          onChanged:
                              (v) => setStateDialog(() => profitCenter = v!),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: refCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Referencia',
                          ),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: receivedByCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Recibido por',
                          ),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: notesCtrl,
                          maxLines: 2,
                          decoration: const InputDecoration(labelText: 'Notas'),
                        ),
                      ],
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      child: const Text('Cancelar'),
                    ),
                    FilledButton(
                      onPressed: () {
                        final amount = double.tryParse(amountCtrl.text.trim());
                        if (descriptionCtrl.text.trim().isEmpty ||
                            amount == null ||
                            amount <= 0) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text(
                                'Descripcion y monto valido son requeridos',
                              ),
                              backgroundColor: DesertBrewColors.error,
                            ),
                          );
                          return;
                        }
                        final payload = {
                          'income_type': incomeType,
                          'category': category,
                          'description': descriptionCtrl.text.trim(),
                          'amount': amount,
                          'payment_method': paymentMethod,
                          'profit_center': profitCenter,
                          if (refCtrl.text.trim().isNotEmpty)
                            'reference_id': refCtrl.text.trim(),
                          if (receivedByCtrl.text.trim().isNotEmpty)
                            'received_by': receivedByCtrl.text.trim(),
                          if (notesCtrl.text.trim().isNotEmpty)
                            'notes': notesCtrl.text.trim(),
                        };
                        if (existing == null) {
                          context.read<IncomeBloc>().add(
                            IncomeCreateRequested(payload),
                          );
                        } else {
                          context.read<IncomeBloc>().add(
                            IncomeUpdateRequested(
                              id: existing.id,
                              payload: payload,
                            ),
                          );
                        }
                        Navigator.of(ctx).pop();
                      },
                      child: Text(existing == null ? 'Crear' : 'Guardar'),
                    ),
                  ],
                ),
          ),
    );
    descriptionCtrl.dispose();
    amountCtrl.dispose();
    refCtrl.dispose();
    notesCtrl.dispose();
    receivedByCtrl.dispose();
  }

  Future<void> _confirmDeleteIncome(IncomeEntry income) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Eliminar ingreso'),
            content: Text('Se eliminara "${income.description}".'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                child: const Text('Eliminar'),
              ),
            ],
          ),
    );
    if (!mounted) return;
    if (confirmed == true) {
      context.read<IncomeBloc>().add(IncomeDeleteRequested(income.id));
    }
  }
}

class _IncomeTile extends StatelessWidget {
  const _IncomeTile({
    required this.income,
    required this.onEdit,
    required this.onDelete,
  });
  final IncomeEntry income;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  Color get _methodColor {
    switch (income.paymentMethod) {
      case 'card':
        return DesertBrewColors.primary;
      case 'cash':
        return DesertBrewColors.success;
      case 'transfer':
        return DesertBrewColors.accent;
      default:
        return DesertBrewColors.textHint;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final fmt = DateFormat('dd/MM/yy HH:mm');
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: DesertBrewColors.success.withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: DesertBrewColors.success.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.trending_up_rounded,
              color: DesertBrewColors.success,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  income.description,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 5,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: _methodColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(5),
                      ),
                      child: Text(
                        income.paymentMethod,
                        style: TextStyle(color: _methodColor, fontSize: 9),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      income.profitCenter,
                      style: const TextStyle(
                        color: DesertBrewColors.textHint,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
                Text(
                  fmt.format(income.receivedDate),
                  style: const TextStyle(
                    color: DesertBrewColors.textHint,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                currency.format(income.amount),
                style: const TextStyle(
                  color: DesertBrewColors.success,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              PopupMenuButton<String>(
                onSelected: (v) => v == 'edit' ? onEdit() : onDelete(),
                itemBuilder:
                    (_) => const [
                      PopupMenuItem(value: 'edit', child: Text('Editar')),
                      PopupMenuItem(value: 'delete', child: Text('Eliminar')),
                    ],
                icon: const Icon(
                  Icons.more_vert_rounded,
                  size: 18,
                  color: DesertBrewColors.textHint,
                ),
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
  Widget build(BuildContext context) => Expanded(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          value,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 13,
          ),
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
        ),
        Text(
          label,
          style: const TextStyle(color: DesertBrewColors.textHint, fontSize: 9),
          textAlign: TextAlign.center,
        ),
      ],
    ),
  );
}
