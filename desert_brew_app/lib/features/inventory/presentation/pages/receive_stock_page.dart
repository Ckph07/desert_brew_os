import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/inventory_remote_datasource.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/ingredient_catalog_item.dart';
import '../bloc/stock/stock_bloc.dart';
import '../bloc/supplier/supplier_bloc.dart';

class ReceiveStockPage extends StatefulWidget {
  const ReceiveStockPage({super.key});

  @override
  State<ReceiveStockPage> createState() => _ReceiveStockPageState();
}

class _ReceiveStockPageState extends State<ReceiveStockPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _quantityController = TextEditingController();
  final _unitCostController = TextEditingController();
  final _batchNumberController = TextEditingController();
  final _notesController = TextEditingController();
  final InventoryRepositoryImpl _repo = InventoryRepositoryImpl(
    InventoryRemoteDataSource(),
  );

  String _category = 'MALT';
  String _unit = 'KG';
  int? _selectedSupplierId;
  int? _selectedIngredientId;
  bool _loadingIngredients = false;
  String? _ingredientsError;
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

  IngredientCatalogItem? get _selectedIngredient {
    if (_selectedIngredientId == null) return null;
    for (final ingredient in _ingredients) {
      if (ingredient.id == _selectedIngredientId) return ingredient;
    }
    return null;
  }

  @override
  void initState() {
    super.initState();
    _loadIngredients();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _unitCostController.dispose();
    _batchNumberController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _loadIngredients() async {
    setState(() {
      _loadingIngredients = true;
      _ingredientsError = null;
    });
    try {
      final items = await _repo.getIngredients(activeOnly: true, limit: 500);
      if (!mounted) return;
      setState(() {
        _ingredients = items;
        if (_selectedIngredientId != null &&
            !_ingredients.any((it) => it.id == _selectedIngredientId)) {
          _selectedIngredientId = null;
          _nameController.clear();
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _ingredientsError = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loadingIngredients = false);
      }
    }
  }

  void _applySelectedIngredient(IngredientCatalogItem ingredient) {
    _nameController.text = ingredient.sku;
    _category = ingredient.category;
    _unit = ingredient.unitMeasure;
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => StockBloc(_repo)),
        BlocProvider(
          create: (_) => SupplierBloc(_repo)..add(SupplierLoadRequested()),
        ),
      ],
      child: BlocListener<StockBloc, StockState>(
        listener: (context, state) {
          if (state is StockReceiveSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  '✓ ${state.newBatch.ingredientName} recibido correctamente',
                ),
                backgroundColor: DesertBrewColors.success,
              ),
            );
            context.pop();
          } else if (state is StockError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Error: ${state.message}'),
                backgroundColor: DesertBrewColors.error,
              ),
            );
          }
        },
        child: Scaffold(
          appBar: AppBar(
            title: const Text('Recibir Materia Prima'),
            actions: [
              IconButton(
                icon: const Icon(Icons.list_alt_rounded),
                tooltip: 'Catalogo de insumos',
                onPressed: () async {
                  await context.push('/inventory/ingredients');
                  if (mounted) {
                    _loadIngredients();
                  }
                },
              ),
            ],
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  DropdownButtonFormField<int?>(
                    value: _selectedIngredientId,
                    decoration: const InputDecoration(
                      labelText: 'Insumo de catalogo',
                      prefixIcon: Icon(Icons.inventory_2_rounded),
                    ),
                    items: [
                      const DropdownMenuItem<int?>(
                        value: null,
                        child: Text('Captura manual'),
                      ),
                      ..._ingredients.map(
                        (ingredient) => DropdownMenuItem<int?>(
                          value: ingredient.id,
                          child: Text(
                            '${ingredient.name} (${ingredient.sku})',
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                    onChanged: (value) {
                      setState(() {
                        _selectedIngredientId = value;
                        if (value == null) {
                          _nameController.clear();
                        } else {
                          final ingredient = _selectedIngredient;
                          if (ingredient != null) {
                            _applySelectedIngredient(ingredient);
                          }
                        }
                      });
                    },
                  ),
                  if (_loadingIngredients) ...[
                    const SizedBox(height: 6),
                    const LinearProgressIndicator(minHeight: 2),
                  ],
                  if (_ingredientsError != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      'No se pudo cargar el catalogo: $_ingredientsError',
                      style: const TextStyle(
                        color: DesertBrewColors.error,
                        fontSize: 12,
                      ),
                    ),
                  ],
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: () async {
                        await context.push('/inventory/ingredients');
                        if (mounted) {
                          _loadIngredients();
                        }
                      },
                      icon: const Icon(Icons.edit_note_rounded, size: 18),
                      label: const Text('Gestionar catalogo'),
                    ),
                  ),
                  const SizedBox(height: 4),

                  TextFormField(
                    controller: _nameController,
                    enabled: _selectedIngredientId == null,
                    decoration: InputDecoration(
                      labelText:
                          _selectedIngredientId == null
                              ? 'Nombre o SKU del ingrediente *'
                              : 'SKU seleccionado',
                      hintText:
                          _selectedIngredientId == null
                              ? 'Ej: Maris Otter, Cascade Hops'
                              : null,
                      prefixIcon: const Icon(Icons.inventory_rounded),
                    ),
                    validator: (v) {
                      if (_selectedIngredientId != null) return null;
                      return (v == null || v.trim().isEmpty)
                          ? 'Requerido'
                          : null;
                    },
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: _category,
                          decoration: const InputDecoration(
                            labelText: 'Categoria *',
                          ),
                          items:
                              _categories
                                  .map(
                                    (c) => DropdownMenuItem<String>(
                                      value: c,
                                      child: Text(c),
                                    ),
                                  )
                                  .toList(),
                          onChanged: (v) {
                            if (v == null) return;
                            setState(() => _category = v);
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: _unit,
                          decoration: const InputDecoration(
                            labelText: 'Unidad *',
                          ),
                          items:
                              _units
                                  .map(
                                    (u) => DropdownMenuItem<String>(
                                      value: u,
                                      child: Text(u),
                                    ),
                                  )
                                  .toList(),
                          onChanged: (v) {
                            if (v == null) return;
                            setState(() => _unit = v);
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _quantityController,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: const InputDecoration(
                            labelText: 'Cantidad *',
                            prefixIcon: Icon(Icons.scale_rounded),
                          ),
                          validator: (v) {
                            if (v == null || v.isEmpty) {
                              return 'Requerido';
                            }
                            if (double.tryParse(v) == null) {
                              return 'Numero invalido';
                            }
                            return null;
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextFormField(
                          controller: _unitCostController,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: const InputDecoration(
                            labelText: 'Costo unitario \$*',
                            prefixIcon: Icon(Icons.attach_money_rounded),
                          ),
                          validator: (v) {
                            if (v == null || v.isEmpty) {
                              return 'Requerido';
                            }
                            if (double.tryParse(v) == null) {
                              return 'Numero invalido';
                            }
                            return null;
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  BlocBuilder<SupplierBloc, SupplierState>(
                    builder: (context, state) {
                      final suppliers =
                          state is SupplierLoaded
                              ? state.suppliers
                              : <dynamic>[];
                      return DropdownButtonFormField<int?>(
                        value: _selectedSupplierId,
                        decoration: const InputDecoration(
                          labelText: 'Proveedor (opcional)',
                          prefixIcon: Icon(Icons.business_rounded),
                        ),
                        items: [
                          const DropdownMenuItem<int?>(
                            value: null,
                            child: Text('Sin proveedor'),
                          ),
                          ...suppliers.map(
                            (s) => DropdownMenuItem<int?>(
                              value: s.id as int,
                              child: Text(s.name as String),
                            ),
                          ),
                        ],
                        onChanged:
                            (v) => setState(() => _selectedSupplierId = v),
                      );
                    },
                  ),
                  const SizedBox(height: 16),

                  TextFormField(
                    controller: _batchNumberController,
                    decoration: const InputDecoration(
                      labelText: 'Numero de lote (opcional)',
                      prefixIcon: Icon(Icons.tag_rounded),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _notesController,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Notas (opcional)',
                      prefixIcon: Icon(Icons.notes_rounded),
                    ),
                  ),
                  const SizedBox(height: 24),

                  BlocBuilder<StockBloc, StockState>(
                    builder: (context, state) {
                      final isSubmitting = state is StockReceiving;
                      return FilledButton.icon(
                        onPressed: isSubmitting ? null : _submit,
                        icon:
                            isSubmitting
                                ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                                : const Icon(Icons.save_rounded),
                        label: Text(
                          isSubmitting ? 'Guardando...' : 'Recibir Stock',
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;

    final selected = _selectedIngredient;
    final ingredientInput = selected?.sku ?? _nameController.text.trim();
    if (ingredientInput.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Selecciona un insumo o captura nombre/SKU'),
          backgroundColor: DesertBrewColors.warning,
        ),
      );
      return;
    }

    context.read<StockBloc>().add(
      StockReceiveSubmitted(
        ingredientName: ingredientInput,
        category: _category,
        quantity: double.parse(_quantityController.text),
        unit: _unit,
        unitCost: double.parse(_unitCostController.text),
        supplierId: _selectedSupplierId,
        batchNumber:
            _batchNumberController.text.trim().isNotEmpty
                ? _batchNumberController.text.trim()
                : null,
        notes:
            _notesController.text.trim().isNotEmpty
                ? _notesController.text.trim()
                : null,
      ),
    );
  }
}
