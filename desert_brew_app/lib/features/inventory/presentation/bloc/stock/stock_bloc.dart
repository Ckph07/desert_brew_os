import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/entities/stock_batch.dart';
import '../../../domain/entities/stock_summary.dart';
import '../../../domain/repositories/inventory_repository.dart';

part 'stock_event.dart';
part 'stock_state.dart';

class StockBloc extends Bloc<StockEvent, StockState> {
  StockBloc(this._repository) : super(StockInitial()) {
    on<StockLoadRequested>(_onLoad);
    on<StockRefreshRequested>(_onRefresh);
    on<StockReceiveSubmitted>(_onReceive);
  }

  final InventoryRepository _repository;

  // Keep last loaded state for refresh
  List<StockBatch> _batches = [];
  StockSummary _summary = const StockSummary(
      totalBatches: 0, totalValue: 0, lowStockItems: 0, byCategory: {});

  Future<void> _onLoad(
      StockLoadRequested event, Emitter<StockState> emit) async {
    emit(StockLoading());
    try {
      final results = await Future.wait([
        _repository.getStockBatches(
          category: event.category,
          search: event.search,
          lowStockOnly: event.lowStockOnly,
        ),
        _repository.getStockSummary(),
      ]);
      _batches = results[0] as List<StockBatch>;
      _summary = results[1] as StockSummary;
      emit(StockLoaded(
        batches: _batches,
        summary: _summary,
        filterCategory: event.category,
        filterSearch: event.search,
      ));
    } catch (e) {
      emit(StockError(e.toString()));
    }
  }

  Future<void> _onRefresh(
      StockRefreshRequested event, Emitter<StockState> emit) async {
    add(StockLoadRequested());
  }

  Future<void> _onReceive(
      StockReceiveSubmitted event, Emitter<StockState> emit) async {
    emit(StockReceiving(_batches, _summary));
    try {
      final batch = await _repository.receiveStock(
        ingredientName: event.ingredientName,
        category: event.category,
        quantity: event.quantity,
        unit: event.unit,
        unitCost: event.unitCost,
        supplierId: event.supplierId,
        batchNumber: event.batchNumber,
        expiryDate: event.expiryDate,
        notes: event.notes,
      );
      emit(StockReceiveSuccess(batch));
      // Auto-reload after receipt
      add(StockLoadRequested());
    } catch (e) {
      emit(StockError(e.toString()));
    }
  }
}
