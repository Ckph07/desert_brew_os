import 'dart:typed_data';

import '../entities/recipe.dart';
import '../entities/production_batch.dart';
import '../entities/cost_entities.dart';
import '../entities/recipe_stock_validation.dart';

abstract class ProductionRepository {
  // ── Recipes ────────────────────────────────────────────────────────────────
  Future<List<Recipe>> getRecipes({int skip = 0, int limit = 100});
  Future<Recipe> getRecipe(int id);
  Future<Recipe> createRecipe(RecipeDraft draft);
  Future<Recipe> updateRecipe(int id, RecipePatch patch);
  Future<void> deleteRecipe(int id);
  Future<Recipe> importBeerSmithRecipe({
    required Uint8List fileBytes,
    required String fileName,
    int? userId,
  });

  // ── Batches ────────────────────────────────────────────────────────────────
  Future<List<ProductionBatch>> getBatches({
    String? status,
    int skip = 0,
    int limit = 100,
  });
  Future<ProductionBatch> getBatch(int id);
  Future<ProductionBatch> createBatch({
    required int recipeId,
    required String batchNumber,
    required double plannedVolumeLiters,
    String? notes,
  });
  Future<void> startBrewing(int batchId);
  Future<void> startFermenting(int batchId);
  Future<void> startConditioning(int batchId);
  Future<void> startPackaging(int batchId);
  Future<void> cancelBatch({required int batchId, String? reason});
  Future<RecipeStockValidation> validateRecipeStock({
    required int recipeId,
    double? plannedVolumeLiters,
  });
  Future<void> completeBatch({
    required int batchId,
    required double actualVolumeLiters,
    double? actualOg,
    double? actualFg,
  });

  // ── Cost Management ────────────────────────────────────────────────────────
  Future<List<IngredientPrice>> getIngredientPrices();
  Future<List<FixedMonthlyCost>> getFixedCosts();
  Future<CostSummary> getCostSummary();
}
