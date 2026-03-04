import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/config/api_config.dart';
import '../models/stock_batch_model.dart';
import '../models/supplier_model.dart';
import '../models/keg_asset_model.dart';
import '../models/finished_product_model.dart';
import '../models/ingredient_catalog_item_model.dart';

/// Remote data source — all HTTP calls to the Inventory Service on :8001.
class InventoryRemoteDataSource {
  InventoryRemoteDataSource()
    : _dio = ApiClient.forService(ServicePort.inventory);

  final Dio _dio;
  String? _stockSummaryPath;

  // ── Stock ──────────────────────────────────────────────────────────────

  Future<List<StockBatchModel>> getStockBatches({
    String? category,
    String? search,
    bool? lowStockOnly,
    int skip = 0,
    int limit = 100,
  }) async {
    final response = await _dio.get(
      '/api/v1/inventory/stock',
      queryParameters: {
        if (category != null) 'category': category,
        'skip': skip,
        'limit': limit,
      },
    );
    var list =
        (response.data as List<dynamic>)
            .map((e) => StockBatchModel.fromJson(e as Map<String, dynamic>))
            .toList();
    if (search != null && search.trim().isNotEmpty) {
      final query = search.trim().toLowerCase();
      list =
          list
              .where(
                (b) =>
                    b.ingredientName.toLowerCase().contains(query) ||
                    (b.batchNumber ?? '').toLowerCase().contains(query) ||
                    (b.supplierName ?? '').toLowerCase().contains(query),
              )
              .toList();
    }
    if (lowStockOnly == true) {
      list = list.where((b) => b.isLow).toList();
    }
    return list;
  }

  Future<List<Map<String, dynamic>>> getStockSummary() async {
    Future<List<Map<String, dynamic>>> fetchFrom(String path) async {
      final response = await _dio.get(path);
      final list = response.data as List<dynamic>;
      return list.cast<Map<String, dynamic>>();
    }

    if (_stockSummaryPath != null) {
      return fetchFrom(_stockSummaryPath!);
    }

    try {
      final data = await fetchFrom('/api/v1/inventory/summary');
      _stockSummaryPath = '/api/v1/inventory/summary';
      return data;
    } on DioException catch (e) {
      if (e.response?.statusCode != 404) rethrow;
      final data = await fetchFrom('/api/v1/inventory/stock/summary');
      _stockSummaryPath = '/api/v1/inventory/stock/summary';
      return data;
    }
  }

  Future<StockBatchModel> receiveStock(Map<String, dynamic> payload) async {
    final response = await _dio.post('/api/v1/inventory/stock', data: payload);
    return StockBatchModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<StockBatchModel> getStockBatch(int id) async {
    final batches = await getStockBatches(limit: 500);
    return batches.firstWhere(
      (batch) => batch.id == id,
      orElse:
          () =>
              throw DioException(
                requestOptions: RequestOptions(
                  path: '/api/v1/inventory/stock-batches',
                ),
                response: Response(
                  requestOptions: RequestOptions(
                    path: '/api/v1/inventory/stock-batches',
                  ),
                  statusCode: 404,
                  data: {'detail': 'Stock batch $id not found'},
                ),
              ),
    );
  }

  // ── Ingredients Catalog ───────────────────────────────────────────────

  Future<List<IngredientCatalogItemModel>> getIngredients({
    bool activeOnly = true,
    String? search,
    int skip = 0,
    int limit = 200,
  }) async {
    final response = await _dio.get(
      '/api/v1/inventory/ingredients',
      queryParameters: {
        'active_only': activeOnly,
        if (search != null && search.trim().isNotEmpty) 'search': search,
        'skip': skip,
        'limit': limit,
      },
    );
    final list = response.data as List<dynamic>;
    return list
        .map(
          (e) => IngredientCatalogItemModel.fromJson(e as Map<String, dynamic>),
        )
        .toList();
  }

  Future<IngredientCatalogItemModel> createIngredient(
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.post(
      '/api/v1/inventory/ingredients',
      data: payload,
    );
    return IngredientCatalogItemModel.fromJson(
      response.data as Map<String, dynamic>,
    );
  }

  Future<IngredientCatalogItemModel> updateIngredient(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch(
      '/api/v1/inventory/ingredients/$id',
      data: payload,
    );
    return IngredientCatalogItemModel.fromJson(
      response.data as Map<String, dynamic>,
    );
  }

  Future<void> deactivateIngredient(int id) async {
    await _dio.delete('/api/v1/inventory/ingredients/$id');
  }

  // ── Suppliers ──────────────────────────────────────────────────────────

  Future<List<SupplierModel>> getSuppliers({bool activeOnly = true}) async {
    final response = await _dio.get(
      '/api/v1/suppliers',
      queryParameters: {'active_only': activeOnly},
    );
    final list = response.data as List<dynamic>;
    return list
        .map((e) => SupplierModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SupplierModel> getSupplier(int id) async {
    final response = await _dio.get('/api/v1/suppliers/$id');
    return SupplierModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SupplierModel> createSupplier(Map<String, dynamic> payload) async {
    final response = await _dio.post('/api/v1/suppliers', data: payload);
    return SupplierModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SupplierModel> updateSupplier(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch('/api/v1/suppliers/$id', data: payload);
    return SupplierModel.fromJson(response.data as Map<String, dynamic>);
  }

  // ── Kegs ──────────────────────────────────────────────────────────────

  Future<List<KegAssetModel>> getKegs({String? state}) async {
    final res = await _dio.get(
      '/api/v1/inventory/kegs',
      queryParameters: {if (state != null) 'state': state, 'limit': 200},
    );
    return (res.data as List<dynamic>)
        .map((e) => KegAssetModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<KegAssetModel> getKeg(String id) async {
    final res = await _dio.get('/api/v1/inventory/kegs/$id');
    return KegAssetModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> transitionKeg({
    required String kegId,
    required String newState,
    required int userId,
    String? location,
    String? reason,
  }) async {
    await _dio.patch(
      '/api/v1/inventory/kegs/$kegId/transition',
      data: {
        'new_state': newState,
        'user_id': userId,
        if (location != null) 'location': location,
        if (reason != null) 'reason': reason,
      },
    );
  }

  Future<List<KegAssetModel>> getKegsAtRisk({int daysThreshold = 30}) async {
    final res = await _dio.get(
      '/api/v1/inventory/kegs/at-risk',
      queryParameters: {'days_threshold': daysThreshold},
    );
    return (res.data as List<dynamic>)
        .map((e) => KegAssetModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ── Finished Products ──────────────────────────────────────────────────

  Future<List<FinishedProductModel>> getFinishedProducts({
    String? productType,
    String? coldRoomId,
    String? availabilityStatus,
  }) async {
    final res = await _dio.get(
      '/api/v1/inventory/finished-products',
      queryParameters: {
        if (productType != null) 'product_type': productType,
        if (coldRoomId != null) 'cold_room_id': coldRoomId,
        if (availabilityStatus != null)
          'availability_status': availabilityStatus,
        'limit': 200,
      },
    );
    return (res.data as List<dynamic>)
        .map((e) => FinishedProductModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> getFinishedProductSummary() async {
    final res = await _dio.get('/api/v1/inventory/finished-products/summary');
    return res.data as Map<String, dynamic>;
  }

  Future<List<ColdRoomStatusModel>> getColdRoomStatus() async {
    final res = await _dio.get('/api/v1/inventory/cold-room/status');
    final rooms = (res.data['cold_rooms'] as List<dynamic>? ?? []);
    return rooms
        .map((e) => ColdRoomStatusModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
