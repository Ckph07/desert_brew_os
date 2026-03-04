import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/inventory_remote_datasource.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/ingredient_catalog_item.dart';

class IngredientCatalogPage extends StatefulWidget {
  const IngredientCatalogPage({super.key});

  @override
  State<IngredientCatalogPage> createState() => _IngredientCatalogPageState();
}

class _IngredientCatalogPageState extends State<IngredientCatalogPage> {
  final InventoryRepositoryImpl _repo = InventoryRepositoryImpl(
    InventoryRemoteDataSource(),
  );
  final TextEditingController _searchController = TextEditingController();

  bool _activeOnly = true;
  bool _isLoading = false;
  String? _error;
  List<IngredientCatalogItem> _ingredients = const [];

  static const _categories = [
    'MALT',
    'HOPS',
    'YEAST',
    'BOTTLE',
    'CAP',
    'CHEMICAL',
    'LABEL',
    'OTHER',
  ];
  static const _units = ['KG', 'G', 'L', 'ML', 'UNIT'];

  @override
  void initState() {
    super.initState();
    _loadIngredients();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadIngredients() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final items = await _repo.getIngredients(
        activeOnly: _activeOnly,
        search:
            _searchController.text.trim().isEmpty
                ? null
                : _searchController.text.trim(),
      );
      if (!mounted) return;
      setState(() => _ingredients = items);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _createIngredient() async {
    final payload = await _showIngredientFormDialog();
    if (payload == null || !mounted) return;
    try {
      await _repo.createIngredient(
        name: payload['name'] as String,
        category: payload['category'] as String,
        unitMeasure: payload['unit_measure'] as String,
        sku: payload['sku'] as String?,
        notes: payload['notes'] as String?,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Insumo creado'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
      await _loadIngredients();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error creando insumo: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _editIngredient(IngredientCatalogItem item) async {
    final payload = await _showIngredientFormDialog(initial: item);
    if (payload == null || !mounted) return;
    try {
      await _repo.updateIngredient(item.id, payload);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Insumo actualizado'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
      await _loadIngredients();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error actualizando insumo: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _deactivateIngredient(IngredientCatalogItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (ctx) => AlertDialog(
            title: const Text('Desactivar insumo'),
            content: Text('Se desactivara ${item.name} (${item.sku}).'),
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
    if (confirmed != true || !mounted) return;

    try {
      await _repo.deactivateIngredient(item.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Insumo desactivado'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
      await _loadIngredients();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error desactivando insumo: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<Map<String, dynamic>?> _showIngredientFormDialog({
    IngredientCatalogItem? initial,
  }) async {
    final formKey = GlobalKey<FormState>();
    final nameCtrl = TextEditingController(text: initial?.name ?? '');
    final skuCtrl = TextEditingController(text: initial?.sku ?? '');
    final notesCtrl = TextEditingController(text: initial?.notes ?? '');
    var category = initial?.category ?? 'MALT';
    var unit = initial?.unitMeasure ?? 'KG';
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
                          ? 'Nuevo insumo'
                          : 'Editar ${initial.sku}',
                    ),
                    content: SizedBox(
                      width: 480,
                      child: Form(
                        key: formKey,
                        child: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              TextFormField(
                                controller: nameCtrl,
                                decoration: const InputDecoration(
                                  labelText: 'Nombre *',
                                  hintText: 'Ej: Malta Pale',
                                ),
                                validator:
                                    (v) =>
                                        (v == null || v.trim().isEmpty)
                                            ? 'Nombre requerido'
                                            : null,
                              ),
                              const SizedBox(height: 8),
                              TextFormField(
                                controller: skuCtrl,
                                decoration: const InputDecoration(
                                  labelText: 'SKU (opcional)',
                                  hintText: 'Si se omite, se genera del nombre',
                                ),
                              ),
                              const SizedBox(height: 8),
                              DropdownButtonFormField<String>(
                                value: category,
                                decoration: const InputDecoration(
                                  labelText: 'Categoria *',
                                ),
                                items:
                                    _categories
                                        .map(
                                          (c) => DropdownMenuItem(
                                            value: c,
                                            child: Text(c),
                                          ),
                                        )
                                        .toList(),
                                onChanged:
                                    (v) =>
                                        setSt(() => category = v ?? category),
                              ),
                              const SizedBox(height: 8),
                              DropdownButtonFormField<String>(
                                value: unit,
                                decoration: const InputDecoration(
                                  labelText: 'Unidad *',
                                ),
                                items:
                                    _units
                                        .map(
                                          (u) => DropdownMenuItem(
                                            value: u,
                                            child: Text(u),
                                          ),
                                        )
                                        .toList(),
                                onChanged: (v) => setSt(() => unit = v ?? unit),
                              ),
                              const SizedBox(height: 8),
                              TextFormField(
                                controller: notesCtrl,
                                maxLines: 2,
                                decoration: const InputDecoration(
                                  labelText: 'Notas',
                                ),
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
                          if (!formKey.currentState!.validate()) return;
                          result = {
                            'name': nameCtrl.text.trim(),
                            if (skuCtrl.text.trim().isNotEmpty)
                              'sku': skuCtrl.text.trim(),
                            'category': category,
                            'unit_measure': unit,
                            if (notesCtrl.text.trim().isNotEmpty)
                              'notes': notesCtrl.text.trim(),
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
      nameCtrl.dispose();
      skuCtrl.dispose();
      notesCtrl.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Catalogo de Insumos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadIngredients,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 6),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'Buscar por nombre, SKU o categoria',
                      prefixIcon: const Icon(Icons.search_rounded),
                      suffixIcon:
                          _searchController.text.isEmpty
                              ? null
                              : IconButton(
                                icon: const Icon(Icons.clear_rounded),
                                onPressed: () {
                                  _searchController.clear();
                                  _loadIngredients();
                                },
                              ),
                    ),
                    onSubmitted: (_) => _loadIngredients(),
                  ),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Solo activos'),
                  selected: _activeOnly,
                  onSelected: (value) {
                    setState(() => _activeOnly = value);
                    _loadIngredients();
                  },
                ),
              ],
            ),
          ),
          Expanded(
            child: Builder(
              builder: (_) {
                if (_isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (_error != null) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        _error!,
                        style: const TextStyle(color: DesertBrewColors.error),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  );
                }
                if (_ingredients.isEmpty) {
                  return const Center(
                    child: Text(
                      'Sin insumos en catalogo',
                      style: TextStyle(color: DesertBrewColors.textSecondary),
                    ),
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(8),
                  itemCount: _ingredients.length,
                  itemBuilder: (_, i) {
                    final item = _ingredients[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: DesertBrewColors.primary.withValues(
                            alpha: 0.15,
                          ),
                          child: Text(
                            item.name.isEmpty
                                ? '?'
                                : item.name[0].toUpperCase(),
                            style: const TextStyle(
                              color: DesertBrewColors.primary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        title: Text(
                          item.name,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        subtitle: Text(
                          '${item.sku} · ${item.category} · ${item.unitMeasure}'
                          '${item.notes == null ? '' : '\n${item.notes}'}',
                          style: const TextStyle(
                            color: DesertBrewColors.textHint,
                            fontSize: 12,
                          ),
                        ),
                        isThreeLine:
                            item.notes != null && item.notes!.isNotEmpty,
                        trailing: PopupMenuButton<String>(
                          onSelected: (value) {
                            if (value == 'edit') {
                              _editIngredient(item);
                            } else if (value == 'deactivate') {
                              _deactivateIngredient(item);
                            }
                          },
                          itemBuilder:
                              (_) => [
                                const PopupMenuItem(
                                  value: 'edit',
                                  child: Text('Editar'),
                                ),
                                const PopupMenuItem(
                                  value: 'deactivate',
                                  child: Text('Desactivar'),
                                ),
                              ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createIngredient,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo Insumo'),
      ),
    );
  }
}
