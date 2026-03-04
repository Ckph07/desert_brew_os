import 'dart:typed_data';

import '../../domain/entities/recipe.dart';
import '../../domain/entities/production_batch.dart';
import '../../domain/entities/cost_entities.dart';
import '../../domain/entities/recipe_stock_validation.dart';
import '../../domain/repositories/production_repository.dart';
import '../datasources/production_remote_datasource.dart';

class ProductionRepositoryImpl implements ProductionRepository {
  ProductionRepositoryImpl(this._remote);
  final ProductionRemoteDataSource _remote;

  @override
  Future<List<Recipe>> getRecipes({int skip = 0, int limit = 100}) =>
      _remote.getRecipes(skip: skip, limit: limit);

  @override
  Future<Recipe> getRecipe(int id) => _remote.getRecipe(id);

  @override
  Future<Recipe> createRecipe(RecipeDraft draft) => _remote.createRecipe(draft);

  @override
  Future<Recipe> updateRecipe(int id, RecipePatch patch) =>
      _remote.updateRecipe(id, patch);

  @override
  Future<void> deleteRecipe(int id) => _remote.deleteRecipe(id);

  @override
  Future<Recipe> importBeerSmithRecipe({
    required Uint8List fileBytes,
    required String fileName,
    int? userId,
  }) => _remote.importBeerSmithRecipe(
    fileBytes: fileBytes,
    fileName: fileName,
    userId: userId,
  );

  @override
  Future<List<ProductionBatch>> getBatches({
    String? status,
    int skip = 0,
    int limit = 100,
  }) => _remote.getBatches(status: status, skip: skip, limit: limit);

  @override
  Future<ProductionBatch> getBatch(int id) => _remote.getBatch(id);

  @override
  Future<ProductionBatch> createBatch({
    required int recipeId,
    required String batchNumber,
    required double plannedVolumeLiters,
    String? notes,
  }) => _remote.createBatch(
    recipeId: recipeId,
    batchNumber: batchNumber,
    plannedVolumeLiters: plannedVolumeLiters,
    notes: notes,
  );

  @override
  Future<void> startBrewing(int batchId) => _remote.startBrewing(batchId);

  @override
  Future<void> startFermenting(int batchId) => _remote.startFermenting(batchId);

  @override
  Future<void> startConditioning(int batchId) =>
      _remote.startConditioning(batchId);

  @override
  Future<void> startPackaging(int batchId) => _remote.startPackaging(batchId);

  @override
  Future<void> cancelBatch({required int batchId, String? reason}) =>
      _remote.cancelBatch(batchId: batchId, reason: reason);

  @override
  Future<RecipeStockValidation> validateRecipeStock({
    required int recipeId,
    double? plannedVolumeLiters,
  }) => _remote.validateRecipeStock(
    recipeId: recipeId,
    plannedVolumeLiters: plannedVolumeLiters,
  );

  @override
  Future<void> completeBatch({
    required int batchId,
    required double actualVolumeLiters,
    double? actualOg,
    double? actualFg,
  }) => _remote.completeBatch(
    batchId: batchId,
    actualVolumeLiters: actualVolumeLiters,
    actualOg: actualOg,
    actualFg: actualFg,
  );

  @override
  Future<List<IngredientPrice>> getIngredientPrices() =>
      _remote.getIngredientPrices();

  @override
  Future<List<FixedMonthlyCost>> getFixedCosts() => _remote.getFixedCosts();

  @override
  Future<CostSummary> getCostSummary() => _remote.getCostSummary();
}
