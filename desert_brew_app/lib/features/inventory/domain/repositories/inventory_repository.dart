import '../entities/stock_batch.dart';
import '../entities/stock_summary.dart';
import '../entities/supplier.dart';
import '../entities/keg_asset.dart';
import '../entities/finished_product.dart';
import '../entities/ingredient_catalog_item.dart';

/// Abstract repository — defines what operations are possible.
/// The data layer implements this; the BLoC depends only on this interface.
abstract class InventoryRepository {
  // ── Stock ──────────────────────────────────────────────────────────────
  Future<List<StockBatch>> getStockBatches({
    String? category,
    String? search,
    bool? lowStockOnly,
    int skip = 0,
    int limit = 100,
  });

  Future<StockSummary> getStockSummary();

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
  });

  Future<StockBatch> getStockBatch(int id);

  // ── Ingredient Catalog ──────────────────────────────────────────────────
  Future<List<IngredientCatalogItem>> getIngredients({
    bool activeOnly = true,
    String? search,
    int skip = 0,
    int limit = 200,
  });

  Future<IngredientCatalogItem> createIngredient({
    required String name,
    required String category,
    required String unitMeasure,
    String? sku,
    String? notes,
  });

  Future<IngredientCatalogItem> updateIngredient(
    int id,
    Map<String, dynamic> fields,
  );

  Future<void> deactivateIngredient(int id);

  // ── Suppliers ──────────────────────────────────────────────────────────
  Future<List<Supplier>> getSuppliers({bool activeOnly = true});

  Future<Supplier> getSupplier(int id);

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
  });

  Future<Supplier> updateSupplier(int id, Map<String, dynamic> fields);

  // ── Kegs ────────────────────────────────────────────────────────────────────
  Future<List<KegAsset>> getKegs({String? state});
  Future<KegAsset> getKeg(String id);
  Future<void> transitionKeg({
    required String kegId,
    required String newState,
    required int userId,
    String? location,
    String? reason,
  });
  Future<List<KegAsset>> getKegsAtRisk({int daysThreshold = 30});

  // ── Finished Products ──────────────────────────────────────────────────
  Future<List<FinishedProduct>> getFinishedProducts({
    String? productType,
    String? coldRoomId,
    String? availabilityStatus,
  });
  Future<Map<String, dynamic>> getFinishedProductSummary();
  Future<List<ColdRoomStatus>> getColdRoomStatus();
}
