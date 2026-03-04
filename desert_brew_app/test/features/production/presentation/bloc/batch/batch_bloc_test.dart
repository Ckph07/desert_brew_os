import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:desert_brew_app/features/production/domain/entities/cost_entities.dart';
import 'package:desert_brew_app/features/production/domain/entities/production_batch.dart';
import 'package:desert_brew_app/features/production/domain/entities/recipe.dart';
import 'package:desert_brew_app/features/production/domain/entities/recipe_stock_validation.dart';
import 'package:desert_brew_app/features/production/domain/repositories/production_repository.dart';
import 'package:desert_brew_app/features/production/presentation/bloc/batch/batch_bloc.dart';

class _FakeProductionRepository implements ProductionRepository {
  bool completeCalled = false;
  bool startBrewingCalled = false;
  bool createBatchCalled = false;
  bool forceInsufficientStock = false;
  int? lastBatchId;
  double? lastVolume;
  double? lastOg;
  double? lastFg;

  ProductionBatch batch = ProductionBatch(
    id: 42,
    batchNumber: 'IPA-2026-042',
    recipeId: 1,
    recipeName: 'Test IPA',
    status: BatchStatus.planned,
    plannedVolumeLiters: 200,
    plannedAt: DateTime(2026, 1, 1),
    actualVolumeLiters: 190,
    totalCost: 3500,
    costPerLiter: 18.42,
  );

  Recipe recipe = Recipe(
    id: 1,
    name: 'Test IPA',
    style: 'American IPA',
    brewer: 'QA',
    batchSizeLiters: 200,
    fermentables: const [RecipeFermentable(name: 'Pale Malt', amountKg: 5)],
    hops: const [RecipeHop(name: 'Cascade', amountG: 50)],
    yeast: const [
      {'name': 'US-05', 'amount_packets': 1.0},
    ],
    importedAt: DateTime(2026, 1, 1),
    expectedOg: 1.065,
    expectedFg: 1.012,
    expectedAbv: 6.9,
    ibu: 65,
  );

  @override
  Future<void> completeBatch({
    required int batchId,
    required double actualVolumeLiters,
    double? actualOg,
    double? actualFg,
  }) async {
    completeCalled = true;
    lastBatchId = batchId;
    lastVolume = actualVolumeLiters;
    lastOg = actualOg;
    lastFg = actualFg;
  }

  @override
  Future<ProductionBatch> getBatch(int id) async => batch;

  @override
  Future<List<ProductionBatch>> getBatches({
    String? status,
    int skip = 0,
    int limit = 100,
  }) async => [batch];

  @override
  Future<ProductionBatch> createBatch({
    required int recipeId,
    required String batchNumber,
    required double plannedVolumeLiters,
    String? notes,
  }) async {
    createBatchCalled = true;
    return batch;
  }

  @override
  Future<void> startBrewing(int batchId) async {
    startBrewingCalled = true;
  }

  @override
  Future<void> startFermenting(int batchId) async {}

  @override
  Future<void> startConditioning(int batchId) async {}

  @override
  Future<void> startPackaging(int batchId) async {}

  @override
  Future<void> cancelBatch({required int batchId, String? reason}) async {}

  @override
  Future<RecipeStockValidation> validateRecipeStock({
    required int recipeId,
    double? plannedVolumeLiters,
  }) async =>
      forceInsufficientStock
          ? const RecipeStockValidation(
            recipeId: 1,
            recipeName: 'Test',
            scaleFactor: 1,
            plannedVolumeLiters: 20,
            items: [
              RecipeStockValidationItem(
                ingredientType: 'MALT',
                name: 'Pale Malt',
                lookupKey: 'PALE-MALT',
                requiredQuantity: 5,
                unit: 'KG',
                availableQuantity: 0,
                status: StockValidationStatus.insufficient,
                matchedBatches: 0,
              ),
            ],
            allAvailable: false,
          )
          : const RecipeStockValidation(
            recipeId: 1,
            recipeName: 'Test',
            scaleFactor: 1,
            plannedVolumeLiters: 20,
            items: [],
            allAvailable: true,
          );

  @override
  Future<List<Recipe>> getRecipes({int skip = 0, int limit = 100}) async =>
      const [];

  @override
  Future<Recipe> getRecipe(int id) async => recipe;

  @override
  Future<Recipe> createRecipe(RecipeDraft draft) async =>
      throw UnimplementedError();

  @override
  Future<void> deleteRecipe(int id) async {}

  @override
  Future<Recipe> importBeerSmithRecipe({
    required Uint8List fileBytes,
    required String fileName,
    int? userId,
  }) async => throw UnimplementedError();

  @override
  Future<Recipe> updateRecipe(int id, RecipePatch patch) async =>
      throw UnimplementedError();

  @override
  Future<List<IngredientPrice>> getIngredientPrices() async => const [];

  @override
  Future<List<FixedMonthlyCost>> getFixedCosts() async => const [];

  @override
  Future<CostSummary> getCostSummary() async => const CostSummary(
    totalFixedMonthly: 0,
    targetLiters: 0,
    fixedCostPerLiter: 0,
    costBreakdown: [],
    ingredientCount: 0,
  );
}

void main() {
  test(
    'BatchCompleteRequested should call repository and emit BatchDetailLoaded',
    () async {
      final repo = _FakeProductionRepository();
      final bloc = BatchBloc(repo);

      final emitted = <BatchState>[];
      final sub = bloc.stream.listen(emitted.add);

      bloc.add(
        BatchCompleteRequested(
          batchId: 42,
          actualVolumeLiters: 190,
          actualOg: 1.06,
          actualFg: 1.01,
        ),
      );

      await Future<void>.delayed(const Duration(milliseconds: 20));

      expect(repo.completeCalled, isTrue);
      expect(repo.lastBatchId, 42);
      expect(repo.lastVolume, 190);
      expect(repo.lastOg, 1.06);
      expect(repo.lastFg, 1.01);
      expect(emitted.any((s) => s is BatchDetailLoaded), isTrue);

      await sub.cancel();
      await bloc.close();
    },
  );

  test(
    'BatchStartBrewingRequested should stop when stock validation fails',
    () async {
      final repo = _FakeProductionRepository()..forceInsufficientStock = true;
      final bloc = BatchBloc(repo);

      final emitted = <BatchState>[];
      final sub = bloc.stream.listen(emitted.add);

      bloc.add(BatchStartBrewingRequested(42));
      await Future<void>.delayed(const Duration(milliseconds: 30));

      expect(repo.startBrewingCalled, isFalse);
      expect(emitted.any((s) => s is BatchError), isTrue);

      await sub.cancel();
      await bloc.close();
    },
  );

  test(
    'BatchCreateSubmitted should reject recipe out of style profile',
    () async {
      final repo =
          _FakeProductionRepository()
            ..recipe = Recipe(
              id: 1,
              name: 'Broken IPA',
              style: 'American IPA',
              brewer: 'QA',
              batchSizeLiters: 200,
              fermentables: const [
                RecipeFermentable(name: 'Pale Malt', amountKg: 5),
              ],
              hops: const [RecipeHop(name: 'Cascade', amountG: 50)],
              yeast: const [
                {'name': 'US-05', 'amount_packets': 1.0},
              ],
              importedAt: DateTime(2026, 1, 1),
              expectedOg: 1.030,
              expectedFg: 1.020,
              expectedAbv: 2.0,
              ibu: 10,
            );
      final bloc = BatchBloc(repo);

      final emitted = <BatchState>[];
      final sub = bloc.stream.listen(emitted.add);

      bloc.add(
        BatchCreateSubmitted(
          recipeId: 1,
          batchNumber: 'IPA-INVALID-001',
          plannedVolumeLiters: 200,
        ),
      );
      await Future<void>.delayed(const Duration(milliseconds: 30));

      expect(repo.createBatchCalled, isFalse);
      expect(emitted.any((s) => s is BatchError), isTrue);

      await sub.cancel();
      await bloc.close();
    },
  );
}
