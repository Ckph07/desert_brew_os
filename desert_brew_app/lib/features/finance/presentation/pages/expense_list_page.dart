import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/finance_remote_datasource.dart';
import '../../data/repositories/finance_repository_impl.dart';
import '../../domain/entities/expense_entry.dart';
import '../bloc/expense/expense_bloc.dart';

class ExpenseListPage extends StatefulWidget {
  const ExpenseListPage({super.key});
  @override
  State<ExpenseListPage> createState() => _ExpenseListPageState();
}

class _ExpenseListPageState extends State<ExpenseListPage> {
  int _days = 30;
  String? _profitCenter;

  static const _dayOptions = [7, 30, 90, 365];
  static const _pcOptions = <String?>[null, 'factory', 'taproom', 'general'];
  static const _pcLabels = ['Todos', 'Fábrica', 'Taproom', 'General'];
  static const _expenseTypes = [
    'supplier_payment',
    'payroll',
    'purchase',
    'utility',
    'rent',
    'tax',
    'maintenance',
    'other',
  ];
  static const _categories = [
    'raw_materials',
    'packaging',
    'payroll',
    'energy',
    'water',
    'gas',
    'rent',
    'maintenance',
    'transport',
    'marketing',
    'communications',
    'taxes',
    'other',
  ];
  static const _paymentMethods = ['cash', 'card', 'transfer', 'check'];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) => ExpenseBloc(FinanceRepositoryImpl(FinanceRemoteDataSource()))
            ..add(
              ExpenseLoadRequested(days: _days, profitCenter: _profitCenter),
            ),
      child: Builder(builder: _buildBody),
    );
  }

  Widget _buildBody(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Egresos'),
        actions: [
          PopupMenuButton<int>(
            icon: const Icon(Icons.calendar_today_rounded),
            onSelected: (d) {
              setState(() => _days = d);
              context.read<ExpenseBloc>().add(
                ExpenseLoadRequested(days: d, profitCenter: _profitCenter),
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
                () => context.read<ExpenseBloc>().add(
                  ExpenseLoadRequested(
                    days: _days,
                    profitCenter: _profitCenter,
                  ),
                ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openExpenseForm(context),
        child: const Icon(Icons.add_rounded),
      ),
      body: BlocConsumer<ExpenseBloc, ExpenseBlocState>(
        listener: (context, state) {
          if (state is ExpenseActionSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: DesertBrewColors.success,
              ),
            );
          } else if (state is ExpenseError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: DesertBrewColors.error,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is ExpenseLoading || state is ExpenseInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is ExpenseLoaded) {
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
                          currency.format(state.summary.totalExpenses),
                          'Total Egresos',
                          DesertBrewColors.error,
                        ),
                        _KpiCell(
                          '${state.summary.count}',
                          'Registros',
                          DesertBrewColors.primary,
                        ),
                        _KpiCell(
                          state.summary.byCategory.isNotEmpty
                              ? state.summary.byCategory.entries
                                  .reduce((a, b) => a.value > b.value ? a : b)
                                  .key
                              : '—',
                          'Mayor categoría',
                          DesertBrewColors.warning,
                        ),
                      ],
                    ),
                  ),
                ),

                // ── Profit center filter ─────────────────────────────
                SliverToBoxAdapter(
                  child: SizedBox(
                    height: 42,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: _pcOptions.length,
                      itemBuilder:
                          (_, i) => Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: FilterChip(
                              label: Text(
                                _pcLabels[i],
                                style: const TextStyle(fontSize: 11),
                              ),
                              selected: _profitCenter == _pcOptions[i],
                              onSelected: (_) {
                                setState(() => _profitCenter = _pcOptions[i]);
                                context.read<ExpenseBloc>().add(
                                  ExpenseLoadRequested(
                                    days: _days,
                                    profitCenter: _pcOptions[i],
                                  ),
                                );
                              },
                              selectedColor: DesertBrewColors.error.withValues(
                                alpha: 0.2,
                              ),
                            ),
                          ),
                    ),
                  ),
                ),

                // ── Category bars ────────────────────────────────────
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
                                state.summary.totalExpenses > 0
                                    ? e.value / state.summary.totalExpenses
                                    : 0.0;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 6),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 90,
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
                                        backgroundColor: DesertBrewColors.error
                                            .withValues(alpha: 0.1),
                                        valueColor:
                                            const AlwaysStoppedAnimation(
                                              DesertBrewColors.error,
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

                // ── Expense list ─────────────────────────────────────
                state.expenses.isEmpty
                    ? SliverFillRemaining(
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Icon(
                              Icons.trending_down_rounded,
                              size: 48,
                              color: DesertBrewColors.textHint,
                            ),
                            SizedBox(height: 12),
                            Text(
                              'Sin egresos en el período',
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
                          (_, i) => _ExpenseTile(
                            expense: state.expenses[i],
                            onEdit:
                                () => _openExpenseForm(
                                  context,
                                  existing: state.expenses[i],
                                ),
                            onDelete:
                                () => _confirmDeleteExpense(state.expenses[i]),
                          ),
                          childCount: state.expenses.length,
                        ),
                      ),
                    ),
              ],
            );
          }
          if (state is ExpenseError) {
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

  Future<void> _openExpenseForm(
    BuildContext context, {
    ExpenseEntry? existing,
  }) async {
    final descriptionCtrl = TextEditingController(
      text: existing?.description ?? '',
    );
    final amountCtrl = TextEditingController(
      text: existing != null ? existing.amount.toStringAsFixed(2) : '',
    );
    final supplierCtrl = TextEditingController(
      text: existing?.supplierName ?? '',
    );
    final refCtrl = TextEditingController(text: existing?.referenceId ?? '');
    final notesCtrl = TextEditingController(text: existing?.notes ?? '');
    final paidByCtrl = TextEditingController(text: existing?.paidBy ?? '');

    var expenseType = existing?.expenseType ?? _expenseTypes.first;
    var category = existing?.category ?? _categories.first;
    var paymentMethod = existing?.paymentMethod ?? _paymentMethods.first;
    var profitCenter = existing?.profitCenter ?? 'factory';

    await showDialog<void>(
      context: context,
      builder:
          (ctx) => StatefulBuilder(
            builder:
                (ctx, setStateDialog) => AlertDialog(
                  title: Text(
                    existing == null ? 'Nuevo Egreso' : 'Editar Egreso',
                  ),
                  content: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        DropdownButtonFormField<String>(
                          value: expenseType,
                          decoration: const InputDecoration(labelText: 'Tipo'),
                          items:
                              _expenseTypes
                                  .map(
                                    (e) => DropdownMenuItem(
                                      value: e,
                                      child: Text(e),
                                    ),
                                  )
                                  .toList(),
                          onChanged:
                              (v) => setStateDialog(() => expenseType = v!),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          value: category,
                          decoration: const InputDecoration(
                            labelText: 'Categoria',
                          ),
                          items:
                              _categories
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
                              _pcOptions
                                  .whereType<String>()
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
                          controller: supplierCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Proveedor',
                          ),
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
                          controller: paidByCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Pagado por',
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
                          'expense_type': expenseType,
                          'category': category,
                          'description': descriptionCtrl.text.trim(),
                          'amount': amount,
                          'payment_method': paymentMethod,
                          'profit_center': profitCenter,
                          if (supplierCtrl.text.trim().isNotEmpty)
                            'supplier_name': supplierCtrl.text.trim(),
                          if (refCtrl.text.trim().isNotEmpty)
                            'reference_id': refCtrl.text.trim(),
                          if (paidByCtrl.text.trim().isNotEmpty)
                            'paid_by': paidByCtrl.text.trim(),
                          if (notesCtrl.text.trim().isNotEmpty)
                            'notes': notesCtrl.text.trim(),
                        };
                        if (existing == null) {
                          context.read<ExpenseBloc>().add(
                            ExpenseCreateRequested(payload),
                          );
                        } else {
                          context.read<ExpenseBloc>().add(
                            ExpenseUpdateRequested(
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
    supplierCtrl.dispose();
    refCtrl.dispose();
    notesCtrl.dispose();
    paidByCtrl.dispose();
  }

  Future<void> _confirmDeleteExpense(ExpenseEntry expense) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Eliminar egreso'),
            content: Text('Se eliminara "${expense.description}".'),
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
      context.read<ExpenseBloc>().add(ExpenseDeleteRequested(expense.id));
    }
  }
}

class _ExpenseTile extends StatelessWidget {
  const _ExpenseTile({
    required this.expense,
    required this.onEdit,
    required this.onDelete,
  });
  final ExpenseEntry expense;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

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
          color: DesertBrewColors.error.withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: DesertBrewColors.error.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.trending_down_rounded,
              color: DesertBrewColors.error,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  expense.description,
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
                        color: DesertBrewColors.warning.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(5),
                      ),
                      child: Text(
                        expense.categoryDisplayName,
                        style: const TextStyle(
                          color: DesertBrewColors.warning,
                          fontSize: 9,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      expense.profitCenter,
                      style: const TextStyle(
                        color: DesertBrewColors.textHint,
                        fontSize: 10,
                      ),
                    ),
                    if (expense.supplierName != null) ...[
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          '· ${expense.supplierName}',
                          style: const TextStyle(
                            color: DesertBrewColors.textHint,
                            fontSize: 10,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ],
                ),
                Text(
                  fmt.format(expense.paidDate),
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
                currency.format(expense.amount),
                style: const TextStyle(
                  color: DesertBrewColors.error,
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
