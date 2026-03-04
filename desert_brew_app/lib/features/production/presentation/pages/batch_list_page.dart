import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/production_remote_datasource.dart';
import '../../data/repositories/production_repository_impl.dart';
import '../../domain/entities/production_batch.dart';
import '../../domain/entities/style_guidelines.dart';
import '../bloc/batch/batch_bloc.dart';
import '../bloc/recipe/recipe_bloc.dart';

class BatchListPage extends StatefulWidget {
  const BatchListPage({super.key});

  @override
  State<BatchListPage> createState() => _BatchListPageState();
}

class _BatchListPageState extends State<BatchListPage> {
  String? _statusFilter;

  static const _statusOptions = [
    null,
    'planned',
    'brewing',
    'fermenting',
    'conditioning',
    'packaging',
    'completed',
  ];

  static const _statusLabels = [
    'Todos',
    'Planificado',
    'Macerado',
    'Fermentando',
    'Acondicionando',
    'Envasando',
    'Completado',
  ];

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create:
              (_) => BatchBloc(
                ProductionRepositoryImpl(ProductionRemoteDataSource()),
              )..add(BatchLoadRequested(statusFilter: _statusFilter)),
        ),
        BlocProvider(
          create:
              (_) => RecipeBloc(
                ProductionRepositoryImpl(ProductionRemoteDataSource()),
              )..add(RecipeLoadRequested()),
        ),
      ],
      child: Builder(
        builder:
            (context) => Scaffold(
              appBar: AppBar(
                title: const Text('Batches de Producción'),
                actions: [
                  IconButton(
                    icon: const Icon(Icons.refresh_rounded),
                    onPressed:
                        () => context.read<BatchBloc>().add(
                          BatchLoadRequested(statusFilter: _statusFilter),
                        ),
                  ),
                ],
              ),
              floatingActionButton: FloatingActionButton.extended(
                onPressed: () => _showCreateDialog(context),
                icon: const Icon(Icons.add_rounded),
                label: const Text('Nuevo Batch'),
              ),
              body: Column(
                children: [
                  // ── Status filter chips ──────────────────────────
                  SizedBox(
                    height: 44,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: _statusOptions.length,
                      itemBuilder:
                          (_, i) => Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: FilterChip(
                              label: Text(
                                _statusLabels[i],
                                style: const TextStyle(fontSize: 12),
                              ),
                              selected: _statusFilter == _statusOptions[i],
                              onSelected: (_) {
                                setState(
                                  () => _statusFilter = _statusOptions[i],
                                );
                                context.read<BatchBloc>().add(
                                  BatchLoadRequested(
                                    statusFilter: _statusOptions[i],
                                  ),
                                );
                              },
                              selectedColor: DesertBrewColors.primary
                                  .withValues(alpha: 0.2),
                            ),
                          ),
                    ),
                  ),

                  // ── List ─────────────────────────────────────────
                  Expanded(
                    child: BlocBuilder<BatchBloc, BatchState>(
                      builder: (context, state) {
                        if (state is BatchLoading || state is BatchInitial) {
                          return const Center(
                            child: CircularProgressIndicator(),
                          );
                        }
                        if (state is BatchError) {
                          return Center(
                            child: Text(
                              state.message,
                              style: const TextStyle(
                                color: DesertBrewColors.error,
                              ),
                            ),
                          );
                        }
                        if (state is BatchListLoaded) {
                          if (state.batches.isEmpty) {
                            return const Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.science_rounded,
                                    size: 56,
                                    color: DesertBrewColors.textHint,
                                  ),
                                  SizedBox(height: 12),
                                  Text(
                                    'Sin batches',
                                    style: TextStyle(
                                      color: DesertBrewColors.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }
                          return ListView.builder(
                            padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
                            itemCount: state.batches.length,
                            itemBuilder:
                                (_, i) => _BatchTile(batch: state.batches[i]),
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
                  ),
                ],
              ),
            ),
      ),
    );
  }

  void _showCreateDialog(BuildContext ctx) {
    final formKey = GlobalKey<FormState>();
    String batchNumber = '';
    int? recipeId;
    double volumeLiters = 20;

    showDialog(
      context: ctx,
      builder:
          (dCtx) => BlocProvider.value(
            value: ctx.read<RecipeBloc>(),
            child: AlertDialog(
              backgroundColor: DesertBrewColors.surface,
              title: const Text('Nuevo Batch'),
              content: BlocBuilder<RecipeBloc, RecipeState>(
                builder: (_, recipeState) {
                  final recipes =
                      recipeState is RecipeLoaded
                          ? recipeState.recipes
                          : <dynamic>[];
                  return Form(
                    key: formKey,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextFormField(
                          decoration: const InputDecoration(
                            labelText: 'Número de Batch',
                          ),
                          onSaved: (v) => batchNumber = v ?? '',
                          validator:
                              (v) =>
                                  v == null || v.isEmpty ? 'Requerido' : null,
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<int>(
                          decoration: const InputDecoration(
                            labelText: 'Receta',
                          ),
                          items:
                              recipes
                                  .map(
                                    (r) => DropdownMenuItem<int>(
                                      value: r.id,
                                      child: Text(
                                        r.name,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  )
                                  .toList(),
                          onChanged: (v) => recipeId = v,
                          validator:
                              (v) => v == null ? 'Selecciona una receta' : null,
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          initialValue: '20',
                          decoration: const InputDecoration(
                            labelText: 'Volumen Planificado (L)',
                          ),
                          keyboardType: TextInputType.number,
                          validator: (v) {
                            final volume = double.tryParse(v?.trim() ?? '');
                            if (volume == null || volume <= 0) {
                              return 'Volumen inválido';
                            }

                            if (recipeId == null) return null;

                            dynamic selectedRecipe;
                            for (final recipe in recipes) {
                              if (recipe.id == recipeId) {
                                selectedRecipe = recipe;
                                break;
                              }
                            }
                            if (selectedRecipe == null) return null;
                            final recipeWaterProfile =
                                selectedRecipe.waterProfile
                                    as Map<String, dynamic>? ??
                                const <String, dynamic>{};
                            final waterNullable = <String, double?>{
                              'ca':
                                  (recipeWaterProfile['ca'] as num?)
                                      ?.toDouble(),
                              'mg':
                                  (recipeWaterProfile['mg'] as num?)
                                      ?.toDouble(),
                              'na':
                                  (recipeWaterProfile['na'] as num?)
                                      ?.toDouble(),
                              'cl':
                                  (recipeWaterProfile['cl'] as num?)
                                      ?.toDouble(),
                              'so4':
                                  (recipeWaterProfile['so4'] as num?)
                                      ?.toDouble(),
                              'hco3':
                                  (recipeWaterProfile['hco3'] as num?)
                                      ?.toDouble(),
                            };

                            final profile = BeerStyleGuidelines.match(
                              selectedRecipe.style as String?,
                            );
                            if (profile == null) return null;

                            final missing = profile.missingMetrics(
                              expectedOg: selectedRecipe.expectedOg as double?,
                              expectedFg: selectedRecipe.expectedFg as double?,
                              expectedAbv:
                                  selectedRecipe.expectedAbv as double?,
                              ibu: selectedRecipe.ibu as double?,
                            );
                            if (missing.isNotEmpty) {
                              return 'Receta ${profile.name} incompleta: ${missing.join(', ')}';
                            }

                            final missingAdvanced = profile
                                .missingAdvancedMetrics(
                                  colorSrm: selectedRecipe.colorSrm as double?,
                                  waterProfile: waterNullable,
                                );
                            if (missingAdvanced.isNotEmpty) {
                              return 'Receta ${profile.name} incompleta: ${missingAdvanced.join(', ')}';
                            }

                            final targetIssues = profile.validateRecipeTargets(
                              expectedOg: selectedRecipe.expectedOg as double,
                              expectedFg: selectedRecipe.expectedFg as double,
                              expectedAbv: selectedRecipe.expectedAbv as double,
                              ibu: selectedRecipe.ibu as double,
                              colorSrm: selectedRecipe.colorSrm as double,
                            );
                            if (targetIssues.isNotEmpty) {
                              return 'Receta fuera de estilo';
                            }

                            final waterProfile = <String, double>{
                              for (final entry in waterNullable.entries)
                                if (entry.value != null)
                                  entry.key: entry.value!,
                            };
                            final waterIssues = profile.validateWaterProfile(
                              waterProfile,
                            );
                            if (waterIssues.isNotEmpty) {
                              return 'Perfil de agua fuera de estilo';
                            }

                            final volumeIssues = profile.validateBatchScale(
                              recipeBatchSizeLiters:
                                  selectedRecipe.batchSizeLiters as double,
                              plannedVolumeLiters: volume,
                            );
                            if (volumeIssues.isNotEmpty) {
                              return 'Volumen fuera de rango del estilo';
                            }

                            return null;
                          },
                          onSaved:
                              (v) =>
                                  volumeLiters = double.tryParse(v ?? '') ?? 20,
                        ),
                      ],
                    ),
                  );
                },
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dCtx),
                  child: const Text('Cancelar'),
                ),
                FilledButton(
                  onPressed: () {
                    if (formKey.currentState?.validate() ?? false) {
                      formKey.currentState?.save();
                      ctx.read<BatchBloc>().add(
                        BatchCreateSubmitted(
                          recipeId: recipeId!,
                          batchNumber: batchNumber,
                          plannedVolumeLiters: volumeLiters,
                        ),
                      );
                      Navigator.pop(dCtx);
                    }
                  },
                  child: const Text('Crear'),
                ),
              ],
            ),
          ),
    );
  }
}

class _BatchTile extends StatelessWidget {
  const _BatchTile({required this.batch});
  final ProductionBatch batch;

  Color get _statusColor {
    switch (batch.status) {
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
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return GestureDetector(
      onTap:
          () => context.push('/production/batches/${batch.id}', extra: batch),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: DesertBrewColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: _statusColor.withValues(alpha: 0.3)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              // Status dot
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: _statusColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: _statusColor.withValues(alpha: 0.5),
                      blurRadius: 6,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      batch.batchNumber,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                    Text(
                      batch.recipeName,
                      style: const TextStyle(
                        color: DesertBrewColors.textHint,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      color: _statusColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      batch.status.displayName,
                      style: TextStyle(
                        color: _statusColor,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    batch.totalCost != null
                        ? currency.format(batch.totalCost)
                        : '${batch.plannedVolumeLiters.toStringAsFixed(0)} L',
                    style: TextStyle(
                      color:
                          batch.totalCost != null
                              ? DesertBrewColors.success
                              : DesertBrewColors.textHint,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
