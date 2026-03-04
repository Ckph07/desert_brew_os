import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/sales_remote_datasource.dart';
import '../../data/repositories/sales_repository_impl.dart';
import '../../domain/entities/sales_note.dart';
import '../bloc/sales_note/sales_note_bloc.dart';

class SalesNotesPage extends StatelessWidget {
  const SalesNotesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              SalesNoteBloc(SalesRepositoryImpl(SalesRemoteDataSource()))
                ..add(SalesNoteLoadRequested()),
      child: const _SalesNotesView(),
    );
  }
}

class _SalesNotesView extends StatelessWidget {
  const _SalesNotesView();

  static const _statusFilters = [
    (null, 'Todas'),
    ('DRAFT', 'Borrador'),
    ('CONFIRMED', 'Confirmada'),
    ('CANCELLED', 'Cancelada'),
  ];

  static const _paymentFilters = [
    (null, 'Todos pagos'),
    ('PENDING', 'Pendiente'),
    ('PAID', 'Pagada'),
    ('OVERDUE', 'Vencida'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notas de Venta'),
        actions: [
          IconButton(
            tooltip: 'Ver catálogo',
            icon: const Icon(Icons.inventory_2_rounded),
            onPressed: () => context.push('/sales/products'),
          ),
          IconButton(
            tooltip: 'Ver clientes',
            icon: const Icon(Icons.people_alt_rounded),
            onPressed: () => context.push('/sales/clients'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () =>
                    context.read<SalesNoteBloc>().add(SalesNoteLoadRequested()),
          ),
        ],
      ),
      body: Column(
        children: [
          // Status filter row
          SizedBox(
            height: 40,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              children:
                  _statusFilters.map((f) {
                    return BlocBuilder<SalesNoteBloc, SalesNoteState>(
                      builder: (context, state) {
                        final selected =
                            state is SalesNoteLoaded
                                ? state.filterStatus
                                : null;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(
                              f.$2,
                              style: const TextStyle(fontSize: 11),
                            ),
                            selected: selected == f.$1,
                            onSelected:
                                (_) => context.read<SalesNoteBloc>().add(
                                  SalesNoteLoadRequested(status: f.$1),
                                ),
                            selectedColor: DesertBrewColors.primary.withValues(
                              alpha: 0.2,
                            ),
                          ),
                        );
                      },
                    );
                  }).toList(),
            ),
          ),
          // Payment filter row
          SizedBox(
            height: 40,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
              children:
                  _paymentFilters.map((f) {
                    return BlocBuilder<SalesNoteBloc, SalesNoteState>(
                      builder: (context, state) {
                        final selected =
                            state is SalesNoteLoaded
                                ? state.filterPayment
                                : null;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(
                              f.$2,
                              style: const TextStyle(fontSize: 11),
                            ),
                            selected: selected == f.$1,
                            onSelected:
                                (_) => context.read<SalesNoteBloc>().add(
                                  SalesNoteLoadRequested(paymentStatus: f.$1),
                                ),
                            selectedColor: DesertBrewColors.info.withValues(
                              alpha: 0.2,
                            ),
                          ),
                        );
                      },
                    );
                  }).toList(),
            ),
          ),
          const Divider(height: 1),
          // Notes list
          Expanded(
            child: BlocConsumer<SalesNoteBloc, SalesNoteState>(
              listener: (context, state) {
                if (state is SalesNoteActionSuccess) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(state.message),
                      backgroundColor: DesertBrewColors.success,
                    ),
                  );
                } else if (state is SalesNoteError) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(state.message),
                      backgroundColor: DesertBrewColors.error,
                    ),
                  );
                }
              },
              builder: (context, state) {
                if (state is SalesNoteLoading || state is SalesNoteInitial) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is SalesNoteLoaded) {
                  if (state.notes.isEmpty) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.receipt_long_rounded,
                            size: 64,
                            color: DesertBrewColors.textHint,
                          ),
                          SizedBox(height: 12),
                          Text(
                            'Sin notas de venta',
                            style: TextStyle(
                              color: DesertBrewColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.all(8),
                    itemCount: state.notes.length,
                    itemBuilder: (_, i) => _SalesNoteTile(note: state.notes[i]),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/sales/notes/create'),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nueva Nota'),
      ),
    );
  }
}

enum _DraftAction { edit, delete }

class _SalesNoteTile extends StatelessWidget {
  const _SalesNoteTile({required this.note});
  final SalesNote note;
  static const _paymentMethods = [
    'TRANSFERENCIA',
    'EFECTIVO',
    'TARJETA',
    'CHEQUE',
  ];

  Color _statusColor(String status) {
    switch (status) {
      case 'CONFIRMED':
        return DesertBrewColors.success;
      case 'CANCELLED':
        return DesertBrewColors.error;
      default:
        return DesertBrewColors.warning;
    }
  }

  Color _paymentColor(String status) {
    switch (status) {
      case 'PAID':
        return DesertBrewColors.success;
      case 'OVERDUE':
        return DesertBrewColors.error;
      case 'PARTIAL':
        return DesertBrewColors.warning;
      default:
        return DesertBrewColors.textHint;
    }
  }

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('dd MMM yy');
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => context.push('/sales/notes/${note.id}'),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    note.noteNumber,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(width: 8),
                  _StatusBadge(note.status, _statusColor(note.status)),
                  const SizedBox(width: 6),
                  _StatusBadge(
                    note.paymentStatus,
                    _paymentColor(note.paymentStatus),
                  ),
                  if (note.isDraft)
                    PopupMenuButton<_DraftAction>(
                      tooltip: 'Acciones borrador',
                      onSelected: (action) {
                        switch (action) {
                          case _DraftAction.edit:
                            _showEditDraftDialog(context);
                            break;
                          case _DraftAction.delete:
                            _confirmDeleteDraft(context);
                            break;
                        }
                      },
                      itemBuilder:
                          (context) => const [
                            PopupMenuItem(
                              value: _DraftAction.edit,
                              child: ListTile(
                                dense: true,
                                leading: Icon(Icons.edit_rounded),
                                title: Text('Editar'),
                              ),
                            ),
                            PopupMenuItem(
                              value: _DraftAction.delete,
                              child: ListTile(
                                dense: true,
                                leading: Icon(Icons.delete_rounded),
                                title: Text('Eliminar'),
                              ),
                            ),
                          ],
                    ),
                  const Spacer(),
                  Text(
                    currency.format(note.total),
                    style: const TextStyle(
                      color: DesertBrewColors.primary,
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Text(
                    note.clientName ?? '— Sin cliente —',
                    style: const TextStyle(
                      color: DesertBrewColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    fmt.format(note.createdAt.toLocal()),
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                '${note.items.length} líneas · '
                '${note.totalLiters.toStringAsFixed(1)} L · '
                '${note.channel} · ${note.paymentMethod}',
                style: const TextStyle(
                  color: DesertBrewColors.textHint,
                  fontSize: 11,
                ),
              ),
              if (note.isDraft) ...[
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: DesertBrewColors.error,
                      ),
                      onPressed:
                          () => context.read<SalesNoteBloc>().add(
                            SalesNoteCancelRequested(note.id),
                          ),
                      icon: const Icon(Icons.cancel_outlined, size: 16),
                      label: const Text(
                        'Cancelar',
                        style: TextStyle(fontSize: 12),
                      ),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.icon(
                      onPressed:
                          () => context.read<SalesNoteBloc>().add(
                            SalesNoteConfirmRequested(note.id),
                          ),
                      icon: const Icon(Icons.check_circle_rounded, size: 16),
                      label: const Text(
                        'Confirmar',
                        style: TextStyle(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ],
              if (note.isConfirmed && !note.isPaid) ...[
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: DesertBrewColors.success,
                    ),
                    onPressed:
                        () => context.read<SalesNoteBloc>().add(
                          SalesNoteMarkPaidRequested(note.id),
                        ),
                    icon: const Icon(Icons.payments_rounded, size: 16),
                    label: const Text(
                      'Marcar Pagada',
                      style: TextStyle(fontSize: 12),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _confirmDeleteDraft(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Eliminar nota'),
            content: Text(
              'Se eliminará la nota ${note.noteNumber}. Esta acción no se puede deshacer.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                style: FilledButton.styleFrom(
                  backgroundColor: DesertBrewColors.error,
                ),
                child: const Text('Eliminar'),
              ),
            ],
          ),
    );
    if (confirmed != true || !context.mounted) return;
    context.read<SalesNoteBloc>().add(SalesNoteDeleteRequested(note.id));
  }

  Future<void> _showEditDraftDialog(BuildContext context) async {
    final clientNameCtrl = TextEditingController(text: note.clientName ?? '');
    final notesCtrl = TextEditingController(text: note.notes ?? '');
    var includeTaxes = note.includeTaxes;
    var paymentMethod =
        _paymentMethods.contains(note.paymentMethod)
            ? note.paymentMethod
            : _paymentMethods.first;

    try {
      final saved = await showDialog<bool>(
        context: context,
        builder:
            (context) => StatefulBuilder(
              builder:
                  (context, setStateDialog) => AlertDialog(
                    title: Text('Editar ${note.noteNumber}'),
                    content: SingleChildScrollView(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          TextField(
                            controller: clientNameCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Nombre cliente en nota',
                            ),
                          ),
                          const SizedBox(height: 10),
                          DropdownButtonFormField<String>(
                            value: paymentMethod,
                            items:
                                _paymentMethods
                                    .map(
                                      (p) => DropdownMenuItem(
                                        value: p,
                                        child: Text(p),
                                      ),
                                    )
                                    .toList(),
                            onChanged: (v) {
                              if (v == null) return;
                              setStateDialog(() => paymentMethod = v);
                            },
                            decoration: const InputDecoration(
                              labelText: 'Método de pago',
                            ),
                          ),
                          const SizedBox(height: 10),
                          SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text('Incluir impuestos'),
                            dense: true,
                            value: includeTaxes,
                            onChanged: (v) {
                              setStateDialog(() => includeTaxes = v);
                            },
                          ),
                          const SizedBox(height: 8),
                          TextField(
                            controller: notesCtrl,
                            maxLines: 2,
                            decoration: const InputDecoration(
                              labelText: 'Notas',
                            ),
                          ),
                        ],
                      ),
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(false),
                        child: const Text('Cancelar'),
                      ),
                      FilledButton(
                        onPressed: () => Navigator.of(context).pop(true),
                        child: const Text('Guardar'),
                      ),
                    ],
                  ),
            ),
      );
      if (saved != true || !context.mounted) return;

      context.read<SalesNoteBloc>().add(
        SalesNoteUpdateRequested(
          noteId: note.id,
          fields: {
            'client_name':
                clientNameCtrl.text.trim().isEmpty
                    ? null
                    : clientNameCtrl.text.trim(),
            'payment_method': paymentMethod,
            'include_taxes': includeTaxes,
            'notes':
                notesCtrl.text.trim().isEmpty ? null : notesCtrl.text.trim(),
          },
        ),
      );
    } finally {
      clientNameCtrl.dispose();
      notesCtrl.dispose();
    }
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge(this.label, this.color);
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 10)),
    );
  }
}
