import 'package:flutter_test/flutter_test.dart';
import 'package:desert_brew_app/features/inventory/data/datasources/inventory_remote_datasource.dart';
import 'package:desert_brew_app/features/inventory/data/models/stock_batch_model.dart';
import 'package:desert_brew_app/features/inventory/data/repositories/inventory_repository_impl.dart';

class _FakeInventoryRemoteDataSource extends InventoryRemoteDataSource {
  _FakeInventoryRemoteDataSource({
    required this.summaryRows,
    required this.batches,
  });

  final List<Map<String, dynamic>> summaryRows;
  final List<StockBatchModel> batches;

  @override
  Future<List<Map<String, dynamic>>> getStockSummary() async => summaryRows;

  @override
  Future<List<StockBatchModel>> getStockBatches({
    String? category,
    String? search,
    bool? lowStockOnly,
    int skip = 0,
    int limit = 100,
  }) async => batches;
}

void main() {
  group('InventoryRepositoryImpl', () {
    test('normalizeIngredientNameToSku should uppercase and hyphenate', () {
      expect(
        normalizeIngredientNameToSku('Lupulo Cascade pellets'),
        'LUPULO-CASCADE-PELLETS',
      );
      expect(normalizeIngredientNameToSku('  '), 'UNKNOWN');
      expect(normalizeIngredientNameToSku('yeast_us-05'), 'YEAST-US-05');
    });

    test(
      'getStockSummary should aggregate category rows and low stock items',
      () async {
        final repo = InventoryRepositoryImpl(
          _FakeInventoryRemoteDataSource(
            summaryRows: const [
              {
                'category': 'MALT',
                'total_batches': 2,
                'total_quantity': 130.0,
                'total_value_mxn': 2500.0,
              },
              {
                'category': 'HOPS',
                'total_batches': 1,
                'total_quantity': 5.0,
                'total_value_mxn': 900.0,
              },
            ],
            batches: const [
              StockBatchModel(
                id: 1,
                ingredientName: 'MALT-PALE',
                category: 'MALT',
                quantity: 100,
                unit: 'KG',
                unitCost: 15,
                totalCost: 1500,
                remainingQuantity: 50,
              ),
              StockBatchModel(
                id: 2,
                ingredientName: 'HOPS-CASCADE',
                category: 'HOPS',
                quantity: 10,
                unit: 'KG',
                unitCost: 90,
                totalCost: 900,
                remainingQuantity: 1,
              ),
            ],
          ),
        );

        final summary = await repo.getStockSummary();
        expect(summary.totalBatches, 3);
        expect(summary.totalValue, 3400.0);
        expect(summary.byCategory['MALT'], 2500.0);
        expect(summary.byCategory['HOPS'], 900.0);
        expect(summary.lowStockItems, 1);
      },
    );
  });
}
