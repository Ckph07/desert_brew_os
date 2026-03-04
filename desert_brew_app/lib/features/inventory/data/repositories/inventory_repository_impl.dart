import '../../domain/entities/stock_batch.dart';
import '../../domain/entities/stock_summary.dart';
import '../../domain/entities/supplier.dart';
import '../../domain/entities/keg_asset.dart';
import '../../domain/entities/finished_product.dart';
import '../../domain/entities/ingredient_catalog_item.dart';
import '../../domain/repositories/inventory_repository.dart';
import '../datasources/inventory_remote_datasource.dart';
import '../models/supplier_model.dart';
import '../models/ingredient_catalog_item_model.dart';

String normalizeIngredientNameToSku(String ingredientName) {
  final normalized = ingredientName
      .trim()
      .toUpperCase()
      .replaceAll(RegExp(r'[^A-Z0-9]+'), '-')
      .replaceAll(RegExp(r'-+'), '-')
      .replaceAll(RegExp(r'^-|-$'), '');
  return normalized.isEmpty ? 'UNKNOWN' : normalized;
}

/// Concrete implementation of InventoryRepository using the remote datasource.
class InventoryRepositoryImpl implements InventoryRepository {
  InventoryRepositoryImpl(this._remote);

  final InventoryRemoteDataSource _remote;

  // ── Stock ──────────────────────────────────────────────────────────────

  @override
  Future<List<StockBatch>> getStockBatches({
    String? category,
    String? search,
    bool? lowStockOnly,
    int skip = 0,
    int limit = 100,
  }) => _remote.getStockBatches(
    category: category,
    search: search,
    lowStockOnly: lowStockOnly,
    skip: skip,
    limit: limit,
  );

  @override
  Future<StockSummary> getStockSummary() async {
    final raw = await _remote.getStockSummary();
    final batches = await _remote.getStockBatches(limit: 500);
    var totalBatches = 0;
    var totalValue = 0.0;
    final byCategory = <String, double>{};

    for (final row in raw) {
      final category = (row['category'] as String?) ?? 'OTHER';
      final categoryBatches = (row['total_batches'] as num?)?.toInt() ?? 0;
      final categoryValue =
          ((row['total_value_mxn'] ?? row['total_value']) as num?)
              ?.toDouble() ??
          0.0;
      totalBatches += categoryBatches;
      totalValue += categoryValue;
      byCategory[category] = categoryValue;
    }

    return StockSummary(
      totalBatches: totalBatches,
      totalValue: totalValue,
      lowStockItems: batches.where((batch) => batch.isLow).length,
      byCategory: byCategory,
    );
  }

  @override
  Future<StockBatch> receiveStock({
    required String ingredientName,
    required String category,
    required double quantity,
    required String unit,
    required double unitCost,
    int? supplierId,
    String? batchNumber,
    DateTime? expiryDate,
    String? notes,
  }) async {
    String? providerName;
    if (supplierId != null) {
      final supplier = await _remote.getSupplier(supplierId);
      providerName = supplier.name;
    }
    return _remote.receiveStock({
      'sku': normalizeIngredientNameToSku(ingredientName),
      'category': category,
      'quantity': quantity,
      'unit_measure': unit,
      'unit_cost': unitCost,
      if (providerName != null) 'provider_name': providerName,
      if (batchNumber != null) 'batch_number': batchNumber,
      if (expiryDate != null) 'expiration_date': expiryDate.toIso8601String(),
      if (notes != null) 'notes': notes,
    });
  }

  @override
  Future<StockBatch> getStockBatch(int id) => _remote.getStockBatch(id);

  // ── Ingredients Catalog ───────────────────────────────────────────────

  @override
  Future<List<IngredientCatalogItem>> getIngredients({
    bool activeOnly = true,
    String? search,
    int skip = 0,
    int limit = 200,
  }) => _remote.getIngredients(
    activeOnly: activeOnly,
    search: search,
    skip: skip,
    limit: limit,
  );

  @override
  Future<IngredientCatalogItem> createIngredient({
    required String name,
    required String category,
    required String unitMeasure,
    String? sku,
    String? notes,
  }) {
    final safeSku = normalizeIngredientNameToSku(
      sku == null || sku.trim().isEmpty ? name : sku,
    );
    return _remote.createIngredient(
      IngredientCatalogItemModel(
        id: 0,
        sku: safeSku,
        name: name.trim(),
        category: category,
        unitMeasure: unitMeasure,
        notes: notes,
      ).toJson(),
    );
  }

  @override
  Future<IngredientCatalogItem> updateIngredient(
    int id,
    Map<String, dynamic> fields,
  ) {
    final payload = <String, dynamic>{...fields};
    if (payload.containsKey('sku') && payload['sku'] is String) {
      payload['sku'] = normalizeIngredientNameToSku(payload['sku'] as String);
    }
    return _remote.updateIngredient(id, payload);
  }

  @override
  Future<void> deactivateIngredient(int id) => _remote.deactivateIngredient(id);

  // ── Suppliers ──────────────────────────────────────────────────────────

  @override
  Future<List<Supplier>> getSuppliers({bool activeOnly = true}) =>
      _remote.getSuppliers(activeOnly: activeOnly);

  @override
  Future<Supplier> getSupplier(int id) => _remote.getSupplier(id);

  @override
  Future<Supplier> createSupplier({
    required String name,
    String? rfc,
    String? contactName,
    String? phone,
    String? email,
    String? address,
    int? paymentTermsDays,
    double? creditLimit,
    String? notes,
  }) => _remote.createSupplier(
    SupplierModel(
      id: 0, // assigned by server
      name: name,
      rfc: rfc,
      contactName: contactName,
      phone: phone,
      email: email,
      address: address,
      paymentTermsDays: paymentTermsDays,
      creditLimit: creditLimit,
      notes: notes,
    ).toJson(),
  );

  @override
  Future<Supplier> updateSupplier(int id, Map<String, dynamic> fields) =>
      _remote.updateSupplier(id, fields);

  // ── Kegs ──────────────────────────────────────────────────

  @override
  Future<List<KegAsset>> getKegs({String? state}) =>
      _remote.getKegs(state: state);

  @override
  Future<KegAsset> getKeg(String id) => _remote.getKeg(id);

  @override
  Future<void> transitionKeg({
    required String kegId,
    required String newState,
    required int userId,
    String? location,
    String? reason,
  }) => _remote.transitionKeg(
    kegId: kegId,
    newState: newState,
    userId: userId,
    location: location,
    reason: reason,
  );

  @override
  Future<List<KegAsset>> getKegsAtRisk({int daysThreshold = 30}) =>
      _remote.getKegsAtRisk(daysThreshold: daysThreshold);

  // ── Finished Products ───────────────────────────────

  @override
  Future<List<FinishedProduct>> getFinishedProducts({
    String? productType,
    String? coldRoomId,
    String? availabilityStatus,
  }) => _remote.getFinishedProducts(
    productType: productType,
    coldRoomId: coldRoomId,
    availabilityStatus: availabilityStatus,
  );

  @override
  Future<Map<String, dynamic>> getFinishedProductSummary() =>
      _remote.getFinishedProductSummary();

  @override
  Future<List<ColdRoomStatus>> getColdRoomStatus() =>
      _remote.getColdRoomStatus();
}
