import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/production_remote_datasource.dart';
import '../../data/repositories/production_repository_impl.dart';
import '../../domain/entities/production_batch.dart';
import '../../domain/entities/recipe_stock_validation.dart';
import '../bloc/batch/batch_bloc.dart';

class BatchDetailPage extends StatelessWidget {
  const BatchDetailPage({super.key, required this.batchId});
  final int batchId;

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              BatchBloc(ProductionRepositoryImpl(ProductionRemoteDataSource()))
                ..add(BatchDetailRequested(batchId)),
      child: const _BatchDetailView(),
    );
  }
}

class _BatchDetailView extends StatelessWidget {
  const _BatchDetailView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detalle del Batch')),
      body: BlocBuilder<BatchBloc, BatchState>(
        builder: (context, state) {
          if (state is BatchLoading || state is BatchInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is BatchError) {
            return Center(
              child: Text(
                state.message,
                style: const TextStyle(color: DesertBrewColors.error),
              ),
            );
          }
          if (state is BatchDetailLoaded) {
            return _DetailBody(batch: state.batch);
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}

class _DetailBody extends StatelessWidget {
  const _DetailBody({required this.batch});
  final ProductionBatch batch;

  static const _steps = [
    BatchStatus.planned,
    BatchStatus.brewing,
    BatchStatus.fermenting,
    BatchStatus.conditioning,
    BatchStatus.packaging,
    BatchStatus.completed,
  ];

  int get _currentStep {
    final idx = _steps.indexOf(batch.status);
    return idx < 0 ? 0 : idx;
  }

  bool get _canCancel =>
      batch.status != BatchStatus.completed &&
      batch.status != BatchStatus.cancelled;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final bloc = context.read<BatchBloc>();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: DesertBrewColors.surface,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          batch.batchNumber,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          batch.recipeName,
                          style: const TextStyle(
                            color: DesertBrewColors.textHint,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  _StatusBadge(batch.status),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  _Kpi(
                    '${batch.plannedVolumeLiters.toStringAsFixed(0)} L',
                    'Planificado',
                    DesertBrewColors.primary,
                  ),
                  const SizedBox(width: 8),
                  _Kpi(
                    batch.actualVolumeLiters != null
                        ? '${batch.actualVolumeLiters!.toStringAsFixed(1)} L'
                        : '—',
                    'Real',
                    DesertBrewColors.success,
                  ),
                  const SizedBox(width: 8),
                  _Kpi(
                    batch.costPerLiter != null
                        ? '${currency.format(batch.costPerLiter)}/L'
                        : '—',
                    'Costo/L',
                    DesertBrewColors.accent,
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // ── FSM Stepper ───────────────────────────────────────────────────
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: DesertBrewColors.surface,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Etapas de Producción',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: DesertBrewColors.textSecondary,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 12),
              ..._steps.asMap().entries.map((e) {
                final i = e.key;
                final step = e.value;
                final isCompleted = i < _currentStep;
                final isCurrent = i == _currentStep;
                final color =
                    isCurrent
                        ? DesertBrewColors.primary
                        : isCompleted
                        ? DesertBrewColors.success
                        : DesertBrewColors.textHint;

                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      Icon(
                        isCompleted
                            ? Icons.check_circle_rounded
                            : isCurrent
                            ? Icons.radio_button_checked_rounded
                            : Icons.radio_button_unchecked_rounded,
                        color: color,
                        size: 20,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          step.displayName,
                          style: TextStyle(
                            color:
                                isCurrent || isCompleted
                                    ? DesertBrewColors.textPrimary
                                    : DesertBrewColors.textHint,
                            fontWeight:
                                isCurrent ? FontWeight.bold : FontWeight.normal,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // ── Action Button ─────────────────────────────────────────────────
        if (batch.status == BatchStatus.planned)
          Column(
            children: [
              FilledButton.icon(
                onPressed: () => bloc.add(BatchStartBrewingRequested(batch.id)),
                icon: const Icon(Icons.local_fire_department_rounded),
                label: const Text('Iniciar Macerado (BREWING)'),
                style: FilledButton.styleFrom(
                  backgroundColor: DesertBrewColors.warning,
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () => _validateStock(context),
                icon: const Icon(Icons.checklist_rounded),
                label: const Text('Validar Insumos'),
              ),
            ],
          ),
        if (batch.status == BatchStatus.brewing)
          FilledButton.icon(
            onPressed: () => bloc.add(BatchStartFermentingRequested(batch.id)),
            icon: const Icon(Icons.science_rounded),
            label: const Text('Mover a Fermentación'),
            style: FilledButton.styleFrom(
              backgroundColor: DesertBrewColors.accent,
            ),
          ),
        if (batch.status == BatchStatus.fermenting) ...[
          FilledButton.icon(
            onPressed:
                () => bloc.add(BatchStartConditioningRequested(batch.id)),
            icon: const Icon(Icons.ac_unit_rounded),
            label: const Text('Mover a Acondicionamiento'),
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFF8B5CF6),
            ),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () => bloc.add(BatchStartPackagingRequested(batch.id)),
            icon: const Icon(Icons.inventory_2_rounded),
            label: const Text('Saltar a Envasado'),
          ),
        ],
        if (batch.status == BatchStatus.conditioning)
          FilledButton.icon(
            onPressed: () => bloc.add(BatchStartPackagingRequested(batch.id)),
            icon: const Icon(Icons.inventory_2_rounded),
            label: const Text('Mover a Envasado'),
          ),
        if (batch.status == BatchStatus.packaging)
          FilledButton.icon(
            onPressed: () => _showCompleteDialog(context, bloc),
            icon: const Icon(Icons.task_alt_rounded),
            label: const Text('Completar Batch'),
            style: FilledButton.styleFrom(
              backgroundColor: DesertBrewColors.success,
            ),
          ),
        if (_canCancel)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: OutlinedButton.icon(
              onPressed: () => _showCancelDialog(context, bloc),
              icon: const Icon(Icons.cancel_outlined),
              label: const Text('Cancelar Batch'),
              style: OutlinedButton.styleFrom(
                foregroundColor: DesertBrewColors.error,
              ),
            ),
          ),
        const SizedBox(height: 16),

        // ── FIFO Cost Breakdown ───────────────────────────────────────────
        if (batch.costBreakdown != null) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: DesertBrewColors.surface,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Desglose FIFO de Costos',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: DesertBrewColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 12),
                _CostRow(
                  'Malta',
                  batch.maltCost ?? 0,
                  DesertBrewColors.warning,
                  currency,
                ),
                _CostRow(
                  'Lúpulos',
                  batch.hopsCost ?? 0,
                  DesertBrewColors.success,
                  currency,
                ),
                _CostRow(
                  'Levadura',
                  batch.yeastCost ?? 0,
                  DesertBrewColors.accent,
                  currency,
                ),
                _CostRow(
                  'Agua',
                  batch.waterCost ?? 0,
                  DesertBrewColors.primary,
                  currency,
                ),
                _CostRow(
                  'Mano de Obra',
                  batch.laborCost ?? 0,
                  const Color(0xFF8B5CF6),
                  currency,
                ),
                _CostRow(
                  'Overhead',
                  batch.overheadCost ?? 0,
                  DesertBrewColors.textHint,
                  currency,
                ),
                const Divider(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'TOTAL',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      currency.format(batch.costBreakdown!.total),
                      style: const TextStyle(
                        color: DesertBrewColors.success,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],

        // ── Measurements ─────────────────────────────────────────────────
        if (batch.actualOg != null || batch.actualFg != null) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: DesertBrewColors.surface,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Mediciones',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: DesertBrewColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 12),
                if (batch.actualOg != null)
                  _MeasurementRow(
                    'OG Real',
                    batch.actualOg!.toStringAsFixed(3),
                  ),
                if (batch.actualFg != null)
                  _MeasurementRow(
                    'FG Real',
                    batch.actualFg!.toStringAsFixed(3),
                  ),
                if (batch.actualAbv != null)
                  _MeasurementRow(
                    'ABV Real',
                    '${batch.actualAbv!.toStringAsFixed(2)}%',
                  ),
                if (batch.yieldPercentage != null)
                  _MeasurementRow(
                    'Rendimiento',
                    '${batch.yieldPercentage!.toStringAsFixed(1)}%',
                  ),
                if (batch.daysInProduction != null)
                  _MeasurementRow(
                    'Días en producción',
                    '${batch.daysInProduction} días',
                  ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _validateStock(BuildContext context) async {
    final repo = ProductionRepositoryImpl(ProductionRemoteDataSource());

    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final validation = await repo.validateRecipeStock(
        recipeId: batch.recipeId,
        plannedVolumeLiters: batch.plannedVolumeLiters,
      );

      if (context.mounted) {
        Navigator.of(context).pop();
      }
      if (!context.mounted) return;
      await _showValidationResultDialog(context, validation);
    } catch (e) {
      if (context.mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('No se pudo validar inventario: $e'),
            backgroundColor: DesertBrewColors.error,
          ),
        );
      }
    }
  }

  Future<void> _showValidationResultDialog(
    BuildContext context,
    RecipeStockValidation validation,
  ) async {
    Color statusColor(StockValidationStatus status) {
      switch (status) {
        case StockValidationStatus.ok:
          return DesertBrewColors.success;
        case StockValidationStatus.insufficient:
          return DesertBrewColors.warning;
        case StockValidationStatus.missing:
          return DesertBrewColors.error;
      }
    }

    String statusLabel(StockValidationStatus status) {
      switch (status) {
        case StockValidationStatus.ok:
          return 'OK';
        case StockValidationStatus.insufficient:
          return 'INSUFICIENTE';
        case StockValidationStatus.missing:
          return 'NO ENCONTRADO';
      }
    }

    await showDialog<void>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Validación de Insumos'),
            content: SizedBox(
              width: 580,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    validation.allAvailable
                        ? 'Todos los insumos están disponibles.'
                        : 'Se detectaron insumos faltantes o insuficientes.',
                    style: TextStyle(
                      color:
                          validation.allAvailable
                              ? DesertBrewColors.success
                              : DesertBrewColors.warning,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Volumen validado: ${validation.plannedVolumeLiters.toStringAsFixed(1)} L',
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 340),
                    child: ListView.separated(
                      shrinkWrap: true,
                      itemCount: validation.items.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 6),
                      itemBuilder: (_, i) {
                        final item = validation.items[i];
                        final color = statusColor(item.status);
                        return Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: DesertBrewColors.surface,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: color.withValues(alpha: 0.35),
                            ),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item.name,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    Text(
                                      '${item.requiredQuantity.toStringAsFixed(3)} ${item.unit} requerido · '
                                      '${item.availableQuantity.toStringAsFixed(3)} ${item.unit} disponible',
                                      style: const TextStyle(
                                        color: DesertBrewColors.textHint,
                                        fontSize: 11,
                                      ),
                                    ),
                                    Text(
                                      'Lookup: ${item.lookupKey}',
                                      style: const TextStyle(
                                        color: DesertBrewColors.textHint,
                                        fontSize: 10,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Text(
                                statusLabel(item.status),
                                style: TextStyle(
                                  color: color,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              FilledButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cerrar'),
              ),
            ],
          ),
    );
  }

  Future<void> _showCancelDialog(BuildContext context, BatchBloc bloc) async {
    final reasonCtrl = TextEditingController();
    await showDialog<void>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Cancelar Batch'),
            content: TextField(
              controller: reasonCtrl,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Motivo (opcional)',
                hintText: 'Ej. contaminación, error de planificación',
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Volver'),
              ),
              FilledButton(
                onPressed: () {
                  final reason = reasonCtrl.text.trim();
                  Navigator.of(ctx).pop();
                  bloc.add(
                    BatchCancelRequested(
                      batchId: batch.id,
                      reason: reason.isEmpty ? null : reason,
                    ),
                  );
                },
                style: FilledButton.styleFrom(
                  backgroundColor: DesertBrewColors.error,
                ),
                child: const Text('Cancelar Batch'),
              ),
            ],
          ),
    );
    reasonCtrl.dispose();
  }

  Future<void> _showCompleteDialog(BuildContext context, BatchBloc bloc) async {
    final volumeCtrl = TextEditingController(
      text: (batch.actualVolumeLiters ?? batch.plannedVolumeLiters)
          .toStringAsFixed(2),
    );
    final ogCtrl = TextEditingController(
      text: batch.actualOg?.toStringAsFixed(3) ?? '',
    );
    final fgCtrl = TextEditingController(
      text: batch.actualFg?.toStringAsFixed(3) ?? '',
    );
    await showDialog<void>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Completar Batch'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: volumeCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'Volumen real (L)',
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: ogCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'OG (opcional)'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: fgCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'FG (opcional)'),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () {
                  final actualVolume = double.tryParse(volumeCtrl.text.trim());
                  if (actualVolume == null || actualVolume <= 0) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Ingresa un volumen real valido'),
                        backgroundColor: DesertBrewColors.error,
                      ),
                    );
                    return;
                  }
                  final actualOg = double.tryParse(ogCtrl.text.trim());
                  final actualFg = double.tryParse(fgCtrl.text.trim());
                  Navigator.of(ctx).pop();
                  bloc.add(
                    BatchCompleteRequested(
                      batchId: batch.id,
                      actualVolumeLiters: actualVolume,
                      actualOg: actualOg,
                      actualFg: actualFg,
                    ),
                  );
                },
                child: const Text('Completar'),
              ),
            ],
          ),
    );
    volumeCtrl.dispose();
    ogCtrl.dispose();
    fgCtrl.dispose();
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge(this.status);
  final BatchStatus status;

  Color get _color {
    switch (status) {
      case BatchStatus.planned:
        return DesertBrewColors.textHint;
      case BatchStatus.brewing:
        return DesertBrewColors.warning;
      case BatchStatus.fermenting:
        return DesertBrewColors.accent;
      case BatchStatus.conditioning:
        return const Color(0xFF8B5CF6);
      case BatchStatus.packaging:
        return DesertBrewColors.primary;
      case BatchStatus.completed:
        return DesertBrewColors.success;
      case BatchStatus.cancelled:
        return DesertBrewColors.error;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _color.withValues(alpha: 0.3)),
      ),
      child: Text(
        status.displayName,
        style: TextStyle(
          color: _color,
          fontWeight: FontWeight.bold,
          fontSize: 11,
        ),
      ),
    );
  }
}

class _Kpi extends StatelessWidget {
  const _Kpi(this.value, this.label, this.color);
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

class _CostRow extends StatelessWidget {
  const _CostRow(this.label, this.amount, this.color, this.fmt);
  final String label;
  final double amount;
  final Color color;
  final NumberFormat fmt;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: DesertBrewColors.textSecondary,
                fontSize: 12,
              ),
            ),
          ),
          Text(
            fmt.format(amount),
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _MeasurementRow extends StatelessWidget {
  const _MeasurementRow(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: DesertBrewColors.textSecondary,
              fontSize: 12,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              color: DesertBrewColors.textPrimary,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
