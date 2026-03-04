import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/production_remote_datasource.dart';
import '../../data/repositories/production_repository_impl.dart';
import '../../domain/entities/recipe.dart';
import '../../domain/entities/style_guidelines.dart';
import '../bloc/recipe/recipe_bloc.dart';

class RecipeListPage extends StatefulWidget {
  const RecipeListPage({super.key});

  @override
  State<RecipeListPage> createState() => _RecipeListPageState();
}

class _RecipeListPageState extends State<RecipeListPage> {
  late final ProductionRepositoryImpl _repository;
  bool _isMutating = false;

  @override
  void initState() {
    super.initState();
    _repository = ProductionRepositoryImpl(ProductionRemoteDataSource());
  }

  Future<void> _runMutation(Future<void> Function() operation) async {
    if (_isMutating) return;
    setState(() => _isMutating = true);
    try {
      await operation();
      if (!mounted) return;
      context.read<RecipeBloc>().add(RecipeLoadRequested());
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    } finally {
      if (mounted) setState(() => _isMutating = false);
    }
  }

  Future<void> _importBeerSmith() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      withData: true,
      allowedExtensions: ['bsmx'],
    );
    if (result == null || result.files.isEmpty) return;

    final picked = result.files.single;
    final bytes = picked.bytes;
    if (bytes == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo leer el archivo seleccionado'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
      return;
    }

    await _runMutation(
      () => _repository.importBeerSmithRecipe(
        fileBytes: bytes,
        fileName: picked.name,
      ),
    );
  }

  Future<void> _openCreateDialog() async {
    final payload = await showDialog<_RecipeFormData>(
      context: context,
      builder: (_) => const _RecipeEditorDialog(),
    );
    if (payload == null) return;

    await _runMutation(() async {
      await _repository.createRecipe(
        RecipeDraft(
          name: payload.name,
          style: payload.style,
          brewer: payload.brewer,
          batchSizeLiters: payload.batchSizeLiters,
          fermentables:
              payload.fermentables
                  .map(
                    (f) => RecipeFermentable(
                      name: f.name,
                      amountKg: f.amountKg,
                      sku: f.sku,
                      type: f.type,
                    ),
                  )
                  .toList(),
          hops:
              payload.hops
                  .map(
                    (h) => RecipeHop(
                      name: h.name,
                      amountG: h.amountG,
                      sku: h.sku,
                      timeMim: h.timeMin,
                      use: h.use,
                    ),
                  )
                  .toList(),
          yeast:
              payload.yeast
                  .map(
                    (y) => {
                      'name': y.name,
                      if (y.sku != null) 'sku': y.sku,
                      if (y.type != null) 'type': y.type,
                      'amount_packets': y.amountPackets,
                    },
                  )
                  .toList(),
          expectedOg: payload.expectedOg,
          expectedFg: payload.expectedFg,
          expectedAbv: payload.expectedAbv,
          ibu: payload.ibu,
          colorSrm: payload.colorSrm,
          waterProfile: payload.waterProfile,
          notes: payload.notes,
        ),
      );
    });
  }

  Future<void> _openEditDialog(Recipe recipe) async {
    final payload = await showDialog<_RecipeFormData>(
      context: context,
      builder: (_) => _RecipeEditorDialog(recipe: recipe),
    );
    if (payload == null) return;

    await _runMutation(
      () => _repository.updateRecipe(
        recipe.id,
        RecipePatch(
          name: payload.name,
          style: payload.style,
          brewer: payload.brewer,
          batchSizeLiters: payload.batchSizeLiters,
          fermentables:
              payload.fermentables
                  .map(
                    (f) => RecipeFermentable(
                      name: f.name,
                      amountKg: f.amountKg,
                      sku: f.sku,
                      type: f.type,
                    ),
                  )
                  .toList(),
          hops:
              payload.hops
                  .map(
                    (h) => RecipeHop(
                      name: h.name,
                      amountG: h.amountG,
                      sku: h.sku,
                      timeMim: h.timeMin,
                      use: h.use,
                    ),
                  )
                  .toList(),
          yeast:
              payload.yeast
                  .map(
                    (y) => {
                      'name': y.name,
                      if (y.sku != null) 'sku': y.sku,
                      if (y.type != null) 'type': y.type,
                      'amount_packets': y.amountPackets,
                    },
                  )
                  .toList(),
          expectedOg: payload.expectedOg,
          expectedFg: payload.expectedFg,
          expectedAbv: payload.expectedAbv,
          ibu: payload.ibu,
          colorSrm: payload.colorSrm,
          waterProfile: payload.waterProfile,
          notes: payload.notes,
        ),
      ),
    );
  }

  Future<void> _confirmDelete(Recipe recipe) async {
    final shouldDelete = await showDialog<bool>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Eliminar receta'),
            content: Text(
              'Se eliminará "${recipe.name}". Esta acción no se puede deshacer.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                style: FilledButton.styleFrom(
                  backgroundColor: DesertBrewColors.error,
                ),
                child: const Text('Eliminar'),
              ),
            ],
          ),
    );
    if (shouldDelete != true) return;
    await _runMutation(() => _repository.deleteRecipe(recipe.id));
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => RecipeBloc(_repository)..add(RecipeLoadRequested()),
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Recetas'),
          actions: [
            IconButton(
              icon: const Icon(Icons.file_upload_rounded),
              tooltip: 'Importar BeerSmith (.bsmx)',
              onPressed: _isMutating ? null : _importBeerSmith,
            ),
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              onPressed:
                  _isMutating
                      ? null
                      : () =>
                          context.read<RecipeBloc>().add(RecipeLoadRequested()),
            ),
          ],
          bottom:
              _isMutating
                  ? const PreferredSize(
                    preferredSize: Size.fromHeight(2),
                    child: LinearProgressIndicator(minHeight: 2),
                  )
                  : null,
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: _isMutating ? null : _openCreateDialog,
          icon: const Icon(Icons.add_rounded),
          label: const Text('Nueva Receta'),
        ),
        body: BlocBuilder<RecipeBloc, RecipeState>(
          builder: (context, state) {
            if (state is RecipeLoading || state is RecipeInitial) {
              return const Center(child: CircularProgressIndicator());
            }
            if (state is RecipeError) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.wifi_off_rounded,
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
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed:
                          () => context.read<RecipeBloc>().add(
                            RecipeLoadRequested(),
                          ),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Reintentar'),
                    ),
                  ],
                ),
              );
            }
            if (state is RecipeLoaded) {
              if (state.recipes.isEmpty) {
                return const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.book_rounded,
                        size: 56,
                        color: DesertBrewColors.textHint,
                      ),
                      SizedBox(height: 12),
                      Text(
                        'Sin recetas registradas',
                        style: TextStyle(color: DesertBrewColors.textSecondary),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Crea manualmente o importa un archivo .bsmx',
                        style: TextStyle(
                          color: DesertBrewColors.textHint,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: state.recipes.length,
                itemBuilder:
                    (_, i) => _RecipeTile(
                      recipe: state.recipes[i],
                      onTap:
                          () => context.push(
                            '/production/recipes/${state.recipes[i].id}',
                            extra: state.recipes[i],
                          ),
                      onEdit: () => _openEditDialog(state.recipes[i]),
                      onDelete: () => _confirmDelete(state.recipes[i]),
                    ),
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }
}

class _RecipeTile extends StatelessWidget {
  const _RecipeTile({
    required this.recipe,
    required this.onTap,
    required this.onEdit,
    required this.onDelete,
  });

  final Recipe recipe;
  final VoidCallback onTap;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final abvStr =
        recipe.expectedAbv != null
            ? '${recipe.expectedAbv!.toStringAsFixed(1)}%'
            : '—';
    final ibuStr =
        recipe.ibu != null ? '${recipe.ibu!.toStringAsFixed(0)} IBU' : '—';

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: DesertBrewColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: DesertBrewColors.primary.withValues(alpha: 0.15),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: DesertBrewColors.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      Icons.book_rounded,
                      color: DesertBrewColors.primary,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          recipe.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                        if (recipe.style != null)
                          Text(
                            recipe.style!,
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
                      Text(
                        '${recipe.batchSizeLiters.toStringAsFixed(0)} L',
                        style: const TextStyle(
                          color: DesertBrewColors.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        DateFormat('dd/MM/yy').format(recipe.importedAt),
                        style: const TextStyle(
                          color: DesertBrewColors.textHint,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'edit') onEdit();
                      if (value == 'delete') onDelete();
                    },
                    itemBuilder:
                        (ctx) => const [
                          PopupMenuItem(value: 'edit', child: Text('Editar')),
                          PopupMenuItem(
                            value: 'delete',
                            child: Text('Eliminar'),
                          ),
                        ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  _Chip(
                    Icons.local_bar_rounded,
                    abvStr,
                    DesertBrewColors.accent,
                  ),
                  const SizedBox(width: 8),
                  _Chip(
                    Icons.bubble_chart_rounded,
                    ibuStr,
                    DesertBrewColors.success,
                  ),
                  const SizedBox(width: 8),
                  _Chip(
                    Icons.grain_rounded,
                    '${recipe.totalFermentablesKg.toStringAsFixed(1)} kg',
                    DesertBrewColors.warning,
                  ),
                  const Spacer(),
                  Text(
                    '${recipe.hops.length} lúpulos',
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 11,
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

class _Chip extends StatelessWidget {
  const _Chip(this.icon, this.label, this.color);
  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _FermentableFormData {
  const _FermentableFormData({
    required this.name,
    required this.amountKg,
    this.sku,
    this.type,
  });

  final String name;
  final double amountKg;
  final String? sku;
  final String? type;
}

class _HopFormData {
  const _HopFormData({
    required this.name,
    required this.amountG,
    this.sku,
    this.timeMin,
    this.use,
  });

  final String name;
  final double amountG;
  final String? sku;
  final double? timeMin;
  final String? use;
}

class _YeastFormData {
  const _YeastFormData({
    required this.name,
    required this.amountPackets,
    this.sku,
    this.type,
  });

  final String name;
  final double amountPackets;
  final String? sku;
  final String? type;
}

class _RecipeFormData {
  const _RecipeFormData({
    required this.name,
    required this.batchSizeLiters,
    required this.fermentables,
    required this.hops,
    required this.yeast,
    this.style,
    this.brewer,
    this.expectedOg,
    this.expectedFg,
    this.expectedAbv,
    this.ibu,
    this.colorSrm,
    this.waterProfile,
    this.notes,
  });

  final String name;
  final double batchSizeLiters;
  final List<_FermentableFormData> fermentables;
  final List<_HopFormData> hops;
  final List<_YeastFormData> yeast;
  final String? style;
  final String? brewer;
  final double? expectedOg;
  final double? expectedFg;
  final double? expectedAbv;
  final double? ibu;
  final double? colorSrm;
  final Map<String, double>? waterProfile;
  final String? notes;
}

class _FermentableRowControllers {
  _FermentableRowControllers({
    String name = '',
    String sku = '',
    String amountKg = '',
    String type = 'Grain',
  }) : nameCtrl = TextEditingController(text: name),
       skuCtrl = TextEditingController(text: sku),
       amountCtrl = TextEditingController(text: amountKg),
       typeCtrl = TextEditingController(text: type);

  final TextEditingController nameCtrl;
  final TextEditingController skuCtrl;
  final TextEditingController amountCtrl;
  final TextEditingController typeCtrl;

  void dispose() {
    nameCtrl.dispose();
    skuCtrl.dispose();
    amountCtrl.dispose();
    typeCtrl.dispose();
  }
}

class _HopRowControllers {
  _HopRowControllers({
    String name = '',
    String sku = '',
    String amountG = '',
    String timeMin = '',
    String use = 'Boil',
  }) : nameCtrl = TextEditingController(text: name),
       skuCtrl = TextEditingController(text: sku),
       amountCtrl = TextEditingController(text: amountG),
       timeCtrl = TextEditingController(text: timeMin),
       useCtrl = TextEditingController(text: use);

  final TextEditingController nameCtrl;
  final TextEditingController skuCtrl;
  final TextEditingController amountCtrl;
  final TextEditingController timeCtrl;
  final TextEditingController useCtrl;

  void dispose() {
    nameCtrl.dispose();
    skuCtrl.dispose();
    amountCtrl.dispose();
    timeCtrl.dispose();
    useCtrl.dispose();
  }
}

class _YeastRowControllers {
  _YeastRowControllers({
    String name = '',
    String sku = '',
    String type = 'Ale',
    String amountPackets = '1',
  }) : nameCtrl = TextEditingController(text: name),
       skuCtrl = TextEditingController(text: sku),
       typeCtrl = TextEditingController(text: type),
       amountCtrl = TextEditingController(text: amountPackets);

  final TextEditingController nameCtrl;
  final TextEditingController skuCtrl;
  final TextEditingController typeCtrl;
  final TextEditingController amountCtrl;

  void dispose() {
    nameCtrl.dispose();
    skuCtrl.dispose();
    typeCtrl.dispose();
    amountCtrl.dispose();
  }
}

class _RecipeEditorDialog extends StatefulWidget {
  const _RecipeEditorDialog({this.recipe});

  final Recipe? recipe;

  bool get isEditing => recipe != null;

  @override
  State<_RecipeEditorDialog> createState() => _RecipeEditorDialogState();
}

class _RecipeEditorDialogState extends State<_RecipeEditorDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameCtrl;
  late final TextEditingController _styleCtrl;
  late final TextEditingController _brewerCtrl;
  late final TextEditingController _batchSizeCtrl;
  late final TextEditingController _expectedOgCtrl;
  late final TextEditingController _expectedFgCtrl;
  late final TextEditingController _expectedAbvCtrl;
  late final TextEditingController _ibuCtrl;
  late final TextEditingController _colorSrmCtrl;
  late final TextEditingController _waterCaCtrl;
  late final TextEditingController _waterMgCtrl;
  late final TextEditingController _waterNaCtrl;
  late final TextEditingController _waterClCtrl;
  late final TextEditingController _waterSo4Ctrl;
  late final TextEditingController _waterHco3Ctrl;
  late final TextEditingController _notesCtrl;

  final List<_FermentableRowControllers> _fermentables = [];
  final List<_HopRowControllers> _hops = [];
  final List<_YeastRowControllers> _yeast = [];

  BeerStyleProfile? get _styleProfile =>
      BeerStyleGuidelines.match(_styleCtrl.text.trim());

  @override
  void initState() {
    super.initState();
    final recipe = widget.recipe;
    _nameCtrl = TextEditingController(text: recipe?.name ?? '');
    _styleCtrl = TextEditingController(text: recipe?.style ?? '');
    _brewerCtrl = TextEditingController(text: recipe?.brewer ?? '');
    _batchSizeCtrl = TextEditingController(
      text: recipe?.batchSizeLiters.toStringAsFixed(2) ?? '20',
    );
    _expectedOgCtrl = TextEditingController(
      text: recipe?.expectedOg?.toStringAsFixed(3) ?? '',
    );
    _expectedFgCtrl = TextEditingController(
      text: recipe?.expectedFg?.toStringAsFixed(3) ?? '',
    );
    _expectedAbvCtrl = TextEditingController(
      text: recipe?.expectedAbv?.toStringAsFixed(1) ?? '',
    );
    _ibuCtrl = TextEditingController(
      text: recipe?.ibu?.toStringAsFixed(0) ?? '',
    );
    _colorSrmCtrl = TextEditingController(
      text: recipe?.colorSrm?.toStringAsFixed(1) ?? '',
    );
    final waterProfile = recipe?.waterProfile ?? const <String, dynamic>{};
    _waterCaCtrl = TextEditingController(
      text:
          ((waterProfile['ca'] as num?)?.toDouble() ?? 0) > 0
              ? (waterProfile['ca'] as num).toDouble().toStringAsFixed(0)
              : '',
    );
    _waterMgCtrl = TextEditingController(
      text:
          ((waterProfile['mg'] as num?)?.toDouble() ?? 0) > 0
              ? (waterProfile['mg'] as num).toDouble().toStringAsFixed(0)
              : '',
    );
    _waterNaCtrl = TextEditingController(
      text:
          ((waterProfile['na'] as num?)?.toDouble() ?? 0) > 0
              ? (waterProfile['na'] as num).toDouble().toStringAsFixed(0)
              : '',
    );
    _waterClCtrl = TextEditingController(
      text:
          ((waterProfile['cl'] as num?)?.toDouble() ?? 0) > 0
              ? (waterProfile['cl'] as num).toDouble().toStringAsFixed(0)
              : '',
    );
    _waterSo4Ctrl = TextEditingController(
      text:
          ((waterProfile['so4'] as num?)?.toDouble() ?? 0) > 0
              ? (waterProfile['so4'] as num).toDouble().toStringAsFixed(0)
              : '',
    );
    _waterHco3Ctrl = TextEditingController(
      text:
          ((waterProfile['hco3'] as num?)?.toDouble() ?? 0) > 0
              ? (waterProfile['hco3'] as num).toDouble().toStringAsFixed(0)
              : '',
    );
    _notesCtrl = TextEditingController(text: recipe?.notes ?? '');

    if (recipe == null) {
      _fermentables.add(_FermentableRowControllers(amountKg: '5'));
      _yeast.add(_YeastRowControllers());
      return;
    }

    for (final fermentable in recipe.fermentables) {
      _fermentables.add(
        _FermentableRowControllers(
          name: fermentable.name,
          sku: fermentable.sku ?? '',
          amountKg: fermentable.amountKg.toStringAsFixed(3),
          type: fermentable.type ?? 'Grain',
        ),
      );
    }
    for (final hop in recipe.hops) {
      _hops.add(
        _HopRowControllers(
          name: hop.name,
          sku: hop.sku ?? '',
          amountG: hop.amountG.toStringAsFixed(2),
          timeMin: hop.timeMim?.toStringAsFixed(1) ?? '',
          use: hop.use ?? 'Boil',
        ),
      );
    }
    for (final y in recipe.yeast) {
      _yeast.add(
        _YeastRowControllers(
          name: y['name']?.toString() ?? '',
          sku: y['sku']?.toString() ?? '',
          type: y['type']?.toString() ?? 'Ale',
          amountPackets: ((y['amount_packets'] as num?)?.toDouble() ?? 1.0)
              .toStringAsFixed(2),
        ),
      );
    }

    if (_fermentables.isEmpty) _fermentables.add(_FermentableRowControllers());
    if (_yeast.isEmpty) _yeast.add(_YeastRowControllers());
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _styleCtrl.dispose();
    _brewerCtrl.dispose();
    _batchSizeCtrl.dispose();
    _expectedOgCtrl.dispose();
    _expectedFgCtrl.dispose();
    _expectedAbvCtrl.dispose();
    _ibuCtrl.dispose();
    _colorSrmCtrl.dispose();
    _waterCaCtrl.dispose();
    _waterMgCtrl.dispose();
    _waterNaCtrl.dispose();
    _waterClCtrl.dispose();
    _waterSo4Ctrl.dispose();
    _waterHco3Ctrl.dispose();
    _notesCtrl.dispose();
    for (final row in _fermentables) {
      row.dispose();
    }
    for (final row in _hops) {
      row.dispose();
    }
    for (final row in _yeast) {
      row.dispose();
    }
    super.dispose();
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: DesertBrewColors.error),
    );
  }

  List<_FermentableFormData>? _collectFermentables() {
    final items = <_FermentableFormData>[];
    for (final row in _fermentables) {
      final name = row.nameCtrl.text.trim();
      final sku = row.skuCtrl.text.trim();
      final amountText = row.amountCtrl.text.trim();
      final type = row.typeCtrl.text.trim();
      final isEmpty =
          name.isEmpty && sku.isEmpty && amountText.isEmpty && type.isEmpty;
      if (isEmpty) continue;

      final amount = double.tryParse(amountText);
      if (name.isEmpty || amount == null || amount <= 0) {
        _showError('Cada fermentable requiere nombre y cantidad (kg) > 0.');
        return null;
      }

      items.add(
        _FermentableFormData(
          name: name,
          amountKg: amount,
          sku: sku.isEmpty ? null : sku,
          type: type.isEmpty ? null : type,
        ),
      );
    }
    if (items.isEmpty) {
      _showError('Agrega al menos un fermentable.');
      return null;
    }
    return items;
  }

  List<_HopFormData>? _collectHops() {
    final items = <_HopFormData>[];
    for (final row in _hops) {
      final name = row.nameCtrl.text.trim();
      final sku = row.skuCtrl.text.trim();
      final amountText = row.amountCtrl.text.trim();
      final timeText = row.timeCtrl.text.trim();
      final use = row.useCtrl.text.trim();
      final isEmpty =
          name.isEmpty &&
          sku.isEmpty &&
          amountText.isEmpty &&
          timeText.isEmpty &&
          use.isEmpty;
      if (isEmpty) continue;

      final amount = double.tryParse(amountText);
      final time = timeText.isEmpty ? null : double.tryParse(timeText);
      if (name.isEmpty || amount == null || amount <= 0) {
        _showError('Cada lúpulo requiere nombre y cantidad (g) > 0.');
        return null;
      }
      if (timeText.isNotEmpty && (time == null || time < 0)) {
        _showError('El tiempo de lúpulo debe ser un número >= 0.');
        return null;
      }

      items.add(
        _HopFormData(
          name: name,
          amountG: amount,
          sku: sku.isEmpty ? null : sku,
          timeMin: time,
          use: use.isEmpty ? null : use,
        ),
      );
    }
    return items;
  }

  List<_YeastFormData>? _collectYeast() {
    final items = <_YeastFormData>[];
    for (final row in _yeast) {
      final name = row.nameCtrl.text.trim();
      final sku = row.skuCtrl.text.trim();
      final type = row.typeCtrl.text.trim();
      final amountText = row.amountCtrl.text.trim();
      final isEmpty =
          name.isEmpty && sku.isEmpty && type.isEmpty && amountText.isEmpty;
      if (isEmpty) continue;

      final amount =
          amountText.isEmpty ? 1.0 : double.tryParse(amountText.trim());
      if (name.isEmpty || amount == null || amount <= 0) {
        _showError('Cada levadura requiere nombre y cantidad de paquetes > 0.');
        return null;
      }

      items.add(
        _YeastFormData(
          name: name,
          amountPackets: amount,
          sku: sku.isEmpty ? null : sku,
          type: type.isEmpty ? null : type,
        ),
      );
    }
    if (items.isEmpty) {
      _showError('Agrega al menos una levadura.');
      return null;
    }
    return items;
  }

  double? _parseOptionalDouble({
    required String raw,
    required String label,
    required double min,
  }) {
    final text = raw.trim();
    if (text.isEmpty) return null;
    final value = double.tryParse(text);
    if (value == null || value < min) {
      _showError('$label inválido. Debe ser numérico y >= $min.');
      return double.nan;
    }
    return value;
  }

  Map<String, double?> _collectWaterProfileNullable() {
    return {
      'ca': _parseOptionalDouble(
        raw: _waterCaCtrl.text,
        label: 'Calcio (Ca)',
        min: 0,
      ),
      'mg': _parseOptionalDouble(
        raw: _waterMgCtrl.text,
        label: 'Magnesio (Mg)',
        min: 0,
      ),
      'na': _parseOptionalDouble(
        raw: _waterNaCtrl.text,
        label: 'Sodio (Na)',
        min: 0,
      ),
      'cl': _parseOptionalDouble(
        raw: _waterClCtrl.text,
        label: 'Cloruro (Cl)',
        min: 0,
      ),
      'so4': _parseOptionalDouble(
        raw: _waterSo4Ctrl.text,
        label: 'Sulfato (SO4)',
        min: 0,
      ),
      'hco3': _parseOptionalDouble(
        raw: _waterHco3Ctrl.text,
        label: 'Bicarbonato (HCO3)',
        min: 0,
      ),
    };
  }

  Map<String, double> _compactWaterProfile(Map<String, double?> source) {
    final compact = <String, double>{};
    for (final key in BeerStyleGuidelines.waterKeys) {
      final value = source[key];
      if (value != null && !value.isNaN) {
        compact[key] = value;
      }
    }
    return compact;
  }

  void _applyStyleSuggestion() {
    final profile = _styleProfile;
    if (profile == null) {
      _showError('Ingresa un estilo reconocido para sugerir objetivos.');
      return;
    }
    final suggestion = profile.suggestTargets();

    setState(() {
      _expectedOgCtrl.text = suggestion.expectedOg.toStringAsFixed(3);
      _expectedFgCtrl.text = suggestion.expectedFg.toStringAsFixed(3);
      _expectedAbvCtrl.text = suggestion.expectedAbv.toStringAsFixed(1);
      _ibuCtrl.text = suggestion.ibu.toStringAsFixed(0);
      _colorSrmCtrl.text = suggestion.colorSrm.toStringAsFixed(1);
      _waterCaCtrl.text = suggestion.waterProfile.ca.toStringAsFixed(0);
      _waterMgCtrl.text = suggestion.waterProfile.mg.toStringAsFixed(0);
      _waterNaCtrl.text = suggestion.waterProfile.na.toStringAsFixed(0);
      _waterClCtrl.text = suggestion.waterProfile.cl.toStringAsFixed(0);
      _waterSo4Ctrl.text = suggestion.waterProfile.so4.toStringAsFixed(0);
      _waterHco3Ctrl.text = suggestion.waterProfile.hco3.toStringAsFixed(0);
    });
  }

  void _submit() {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final batchSize = double.tryParse(_batchSizeCtrl.text.trim());
    if (batchSize == null || batchSize <= 0) {
      _showError('El volumen de batch debe ser un número mayor a 0.');
      return;
    }

    final fermentables = _collectFermentables();
    if (fermentables == null) return;
    final hops = _collectHops();
    if (hops == null) return;
    final yeast = _collectYeast();
    if (yeast == null) return;

    final expectedOg = _parseOptionalDouble(
      raw: _expectedOgCtrl.text,
      label: 'OG objetivo',
      min: 1.0,
    );
    if (expectedOg != null && expectedOg.isNaN) return;

    final expectedFg = _parseOptionalDouble(
      raw: _expectedFgCtrl.text,
      label: 'FG objetivo',
      min: 1.0,
    );
    if (expectedFg != null && expectedFg.isNaN) return;

    final expectedAbv = _parseOptionalDouble(
      raw: _expectedAbvCtrl.text,
      label: 'ABV objetivo',
      min: 0.0,
    );
    if (expectedAbv != null && expectedAbv.isNaN) return;

    final ibu = _parseOptionalDouble(
      raw: _ibuCtrl.text,
      label: 'IBU objetivo',
      min: 0.0,
    );
    if (ibu != null && ibu.isNaN) return;

    final colorSrm = _parseOptionalDouble(
      raw: _colorSrmCtrl.text,
      label: 'SRM objetivo',
      min: 0.0,
    );
    if (colorSrm != null && colorSrm.isNaN) return;

    final waterProfileNullable = _collectWaterProfileNullable();
    if (waterProfileNullable.values.any(
      (value) => value != null && value.isNaN,
    )) {
      return;
    }

    final styleProfile = _styleProfile;
    if (styleProfile != null) {
      final missing = styleProfile.missingMetrics(
        expectedOg: expectedOg,
        expectedFg: expectedFg,
        expectedAbv: expectedAbv,
        ibu: ibu,
      );
      if (missing.isNotEmpty) {
        _showError(
          'Para estilo ${styleProfile.name} define métricas: ${missing.join(', ')}.',
        );
        return;
      }
      final missingAdvanced = styleProfile.missingAdvancedMetrics(
        colorSrm: colorSrm,
        waterProfile: waterProfileNullable,
      );
      if (missingAdvanced.isNotEmpty) {
        _showError(
          'Para estilo ${styleProfile.name} define: ${missingAdvanced.join(', ')}.',
        );
        return;
      }
      final issues = styleProfile.validateRecipeTargets(
        expectedOg: expectedOg!,
        expectedFg: expectedFg!,
        expectedAbv: expectedAbv!,
        ibu: ibu!,
        colorSrm: colorSrm!,
      );
      if (issues.isNotEmpty) {
        _showError(issues.first);
        return;
      }
      final waterIssues = styleProfile.validateWaterProfile(
        _compactWaterProfile(waterProfileNullable),
      );
      if (waterIssues.isNotEmpty) {
        _showError(waterIssues.first);
        return;
      }
    } else if (expectedOg != null &&
        expectedFg != null &&
        expectedOg <= expectedFg) {
      _showError('OG debe ser mayor que FG.');
      return;
    }

    Navigator.of(context).pop(
      _RecipeFormData(
        name: _nameCtrl.text.trim(),
        style: _styleCtrl.text.trim().isEmpty ? null : _styleCtrl.text.trim(),
        brewer:
            _brewerCtrl.text.trim().isEmpty ? null : _brewerCtrl.text.trim(),
        batchSizeLiters: batchSize,
        fermentables: fermentables,
        hops: hops,
        yeast: yeast,
        expectedOg: expectedOg,
        expectedFg: expectedFg,
        expectedAbv: expectedAbv,
        ibu: ibu,
        colorSrm: colorSrm,
        waterProfile: _compactWaterProfile(waterProfileNullable),
        notes: _notesCtrl.text.trim().isEmpty ? null : _notesCtrl.text.trim(),
      ),
    );
  }

  Widget _sectionHeader(String title, VoidCallback onAdd) {
    return Row(
      children: [
        Expanded(
          child: Text(
            title,
            style: const TextStyle(
              color: DesertBrewColors.textSecondary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        TextButton.icon(
          onPressed: onAdd,
          icon: const Icon(Icons.add_rounded),
          label: const Text('Agregar'),
        ),
      ],
    );
  }

  Widget _buildFermentableRow(int index, _FermentableRowControllers row) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Fermentable ${index + 1}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              IconButton(
                onPressed:
                    _fermentables.length <= 1
                        ? null
                        : () {
                          setState(() {
                            final removed = _fermentables.removeAt(index);
                            removed.dispose();
                          });
                        },
                icon: const Icon(Icons.delete_outline_rounded),
                tooltip: 'Eliminar',
              ),
            ],
          ),
          TextField(
            controller: row.nameCtrl,
            decoration: const InputDecoration(labelText: 'Nombre'),
          ),
          const SizedBox(height: 6),
          TextField(
            controller: row.skuCtrl,
            decoration: const InputDecoration(labelText: 'SKU (opcional)'),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: row.amountCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'Cantidad (kg)'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: row.typeCtrl,
                  decoration: const InputDecoration(labelText: 'Tipo'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHopRow(int index, _HopRowControllers row) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Lúpulo ${index + 1}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              IconButton(
                onPressed: () {
                  setState(() {
                    final removed = _hops.removeAt(index);
                    removed.dispose();
                  });
                },
                icon: const Icon(Icons.delete_outline_rounded),
                tooltip: 'Eliminar',
              ),
            ],
          ),
          TextField(
            controller: row.nameCtrl,
            decoration: const InputDecoration(labelText: 'Nombre'),
          ),
          const SizedBox(height: 6),
          TextField(
            controller: row.skuCtrl,
            decoration: const InputDecoration(labelText: 'SKU (opcional)'),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: row.amountCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'Cantidad (g)'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: row.timeCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'Tiempo (min)'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          TextField(
            controller: row.useCtrl,
            decoration: const InputDecoration(labelText: 'Uso (Boil, Dry Hop)'),
          ),
        ],
      ),
    );
  }

  Widget _buildYeastRow(int index, _YeastRowControllers row) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Levadura ${index + 1}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              IconButton(
                onPressed:
                    _yeast.length <= 1
                        ? null
                        : () {
                          setState(() {
                            final removed = _yeast.removeAt(index);
                            removed.dispose();
                          });
                        },
                icon: const Icon(Icons.delete_outline_rounded),
                tooltip: 'Eliminar',
              ),
            ],
          ),
          TextField(
            controller: row.nameCtrl,
            decoration: const InputDecoration(labelText: 'Nombre'),
          ),
          const SizedBox(height: 6),
          TextField(
            controller: row.skuCtrl,
            decoration: const InputDecoration(labelText: 'SKU (opcional)'),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: row.typeCtrl,
                  decoration: const InputDecoration(labelText: 'Tipo'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: row.amountCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(labelText: 'Paquetes'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.isEditing ? 'Editar Receta' : 'Nueva Receta Manual'),
      content: SizedBox(
        width: 760,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: _nameCtrl,
                  decoration: const InputDecoration(labelText: 'Nombre'),
                  validator:
                      (v) => v == null || v.trim().isEmpty ? 'Requerido' : null,
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _styleCtrl,
                  decoration: const InputDecoration(labelText: 'Estilo'),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _brewerCtrl,
                  decoration: const InputDecoration(labelText: 'Brewer'),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _batchSizeCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'Volumen batch (L)',
                  ),
                  validator: (v) {
                    final val = double.tryParse(v?.trim() ?? '');
                    if (val == null || val <= 0) return 'Volumen inválido';
                    return null;
                  },
                ),
                if (_styleProfile != null) ...[
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: DesertBrewColors.primary.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      'Guía ${_styleProfile!.name}: ${_styleProfile!.rangesLabel()}\n'
                      '${_styleProfile!.waterTargetLabel()}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: DesertBrewColors.textSecondary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: OutlinedButton.icon(
                      onPressed: _applyStyleSuggestion,
                      icon: const Icon(Icons.auto_fix_high_rounded),
                      label: const Text('Aplicar Targets Sugeridos'),
                    ),
                  ),
                ],
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _expectedOgCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'OG objetivo',
                          hintText: '1.060',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: _expectedFgCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'FG objetivo',
                          hintText: '1.012',
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
                        controller: _expectedAbvCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'ABV objetivo (%)',
                          hintText: '6.5',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: _ibuCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'IBU objetivo',
                          hintText: '45',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _colorSrmCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'SRM objetivo',
                    hintText: '8',
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _waterCaCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Ca (ppm)',
                          hintText: '130',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: _waterMgCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Mg (ppm)',
                          hintText: '12',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: _waterNaCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Na (ppm)',
                          hintText: '20',
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
                        controller: _waterClCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Cl (ppm)',
                          hintText: '70',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: _waterSo4Ctrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'SO4 (ppm)',
                          hintText: '220',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextFormField(
                        controller: _waterHco3Ctrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'HCO3 (ppm)',
                          hintText: '50',
                        ),
                      ),
                    ),
                  ],
                ),
                const Divider(height: 24),
                _sectionHeader(
                  'Fermentables',
                  () => setState(
                    () => _fermentables.add(_FermentableRowControllers()),
                  ),
                ),
                ..._fermentables.asMap().entries.map(
                  (e) => _buildFermentableRow(e.key, e.value),
                ),
                const Divider(height: 24),
                _sectionHeader(
                  'Lúpulos',
                  () => setState(() => _hops.add(_HopRowControllers())),
                ),
                ..._hops.asMap().entries.map(
                  (e) => _buildHopRow(e.key, e.value),
                ),
                const Divider(height: 24),
                _sectionHeader(
                  'Levaduras',
                  () => setState(() => _yeast.add(_YeastRowControllers())),
                ),
                ..._yeast.asMap().entries.map(
                  (e) => _buildYeastRow(e.key, e.value),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _notesCtrl,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(labelText: 'Notas'),
                ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: _submit,
          child: Text(widget.isEditing ? 'Guardar Cambios' : 'Guardar'),
        ),
      ],
    );
  }
}
