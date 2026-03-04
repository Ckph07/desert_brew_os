import 'dart:typed_data';
import 'package:dio/dio.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/config/api_config.dart';
import '../../domain/entities/recipe.dart';
import '../models/recipe_model.dart';
import '../models/production_batch_model.dart';
import '../models/cost_models.dart';
import '../models/recipe_stock_validation_model.dart';

/// All HTTP calls to Production Service on :8004.
class ProductionRemoteDataSource {
  ProductionRemoteDataSource()
    : _dio = ApiClient.forService(ServicePort.production);

  final Dio _dio;

  // ── Recipes ──────────────────────────────────────────────────────────────
  Future<List<RecipeModel>> getRecipes({int skip = 0, int limit = 100}) async {
    final res = await _dio.get(
      '/api/v1/production/recipes',
      queryParameters: {'skip': skip, 'limit': limit},
    );
    return (res.data as List<dynamic>)
        .map((e) => RecipeModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RecipeModel> getRecipe(int id) async {
    final res = await _dio.get('/api/v1/production/recipes/$id');
    return RecipeModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<RecipeModel> createRecipe(RecipeDraft draft) async {
    final res = await _dio.post(
      '/api/v1/production/recipes',
      data: draft.toJson(),
    );
    return RecipeModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<RecipeModel> updateRecipe(int id, RecipePatch patch) async {
    final res = await _dio.patch(
      '/api/v1/production/recipes/$id',
      data: patch.toJson(),
    );
    return RecipeModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteRecipe(int id) async {
    await _dio.delete('/api/v1/production/recipes/$id');
  }

  Future<RecipeModel> importBeerSmithRecipe({
    required Uint8List fileBytes,
    required String fileName,
    int? userId,
  }) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(fileBytes, filename: fileName),
    });
    final res = await _dio.post(
      '/api/v1/production/recipes/import',
      queryParameters: {if (userId != null) 'user_id': userId},
      data: form,
    );
    return RecipeModel.fromJson(res.data as Map<String, dynamic>);
  }

  // ── Batches ───────────────────────────────────────────────────────────────
  Future<List<ProductionBatchModel>> getBatches({
    String? status,
    int skip = 0,
    int limit = 100,
  }) async {
    final res = await _dio.get(
      '/api/v1/production/batches',
      queryParameters: {
        'skip': skip,
        'limit': limit,
        if (status != null) 'status': status,
      },
    );
    return (res.data as List<dynamic>)
        .map((e) => ProductionBatchModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ProductionBatchModel> getBatch(int id) async {
    final res = await _dio.get('/api/v1/production/batches/$id');
    return ProductionBatchModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ProductionBatchModel> createBatch({
    required int recipeId,
    required String batchNumber,
    required double plannedVolumeLiters,
    String? notes,
  }) async {
    final res = await _dio.post(
      '/api/v1/production/batches',
      data: {
        'recipe_id': recipeId,
        'batch_number': batchNumber,
        'planned_volume_liters': plannedVolumeLiters,
        if (notes != null) 'notes': notes,
      },
    );
    return ProductionBatchModel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> startBrewing(int batchId) async {
    await _dio.patch('/api/v1/production/batches/$batchId/start-brewing');
  }

  Future<void> startFermenting(int batchId) async {
    await _dio.patch('/api/v1/production/batches/$batchId/start-fermenting');
  }

  Future<void> startConditioning(int batchId) async {
    await _dio.patch('/api/v1/production/batches/$batchId/start-conditioning');
  }

  Future<void> startPackaging(int batchId) async {
    await _dio.patch('/api/v1/production/batches/$batchId/start-packaging');
  }

  Future<void> cancelBatch({required int batchId, String? reason}) async {
    await _dio.patch(
      '/api/v1/production/batches/$batchId/cancel',
      data: {if (reason != null && reason.trim().isNotEmpty) 'reason': reason},
    );
  }

  Future<RecipeStockValidationModel> validateRecipeStock({
    required int recipeId,
    double? plannedVolumeLiters,
  }) async {
    final res = await _dio.post(
      '/api/v1/production/recipes/$recipeId/validate-stock',
      data: {
        if (plannedVolumeLiters != null)
          'planned_volume_liters': plannedVolumeLiters,
      },
    );
    return RecipeStockValidationModel.fromJson(
      res.data as Map<String, dynamic>,
    );
  }

  Future<void> completeBatch({
    required int batchId,
    required double actualVolumeLiters,
    double? actualOg,
    double? actualFg,
  }) async {
    await _dio.patch(
      '/api/v1/production/batches/$batchId/complete',
      data: {
        'actual_volume_liters': actualVolumeLiters,
        if (actualOg != null) 'actual_og': actualOg,
        if (actualFg != null) 'actual_fg': actualFg,
      },
    );
  }

  // ── Cost Management ───────────────────────────────────────────────────────
  Future<List<IngredientPriceModel>> getIngredientPrices() async {
    final res = await _dio.get('/api/v1/production/ingredients');
    return (res.data as List<dynamic>)
        .map((e) => IngredientPriceModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<FixedMonthlyCostModel>> getFixedCosts() async {
    final res = await _dio.get('/api/v1/production/costs/fixed');
    return (res.data as List<dynamic>)
        .map((e) => FixedMonthlyCostModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CostSummaryModel> getCostSummary() async {
    final res = await _dio.get('/api/v1/production/costs/summary');
    return CostSummaryModel.fromJson(res.data as Map<String, dynamic>);
  }
}
