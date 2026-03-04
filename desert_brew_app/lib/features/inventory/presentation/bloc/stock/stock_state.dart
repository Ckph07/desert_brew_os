part of 'stock_bloc.dart';

abstract class StockState {}

class StockInitial extends StockState {}

class StockLoading extends StockState {}

class StockLoaded extends StockState {
  StockLoaded({
    required this.batches,
    required this.summary,
    this.filterCategory,
    this.filterSearch,
  });
  final List<StockBatch> batches;
  final StockSummary summary;
  final String? filterCategory;
  final String? filterSearch;
}

class StockReceiving extends StockState {
  StockReceiving(this.batches, this.summary);
  final List<StockBatch> batches;
  final StockSummary summary;
}

class StockReceiveSuccess extends StockState {
  StockReceiveSuccess(this.newBatch);
  final StockBatch newBatch;
}

class StockError extends StockState {
  StockError(this.message);
  final String message;
}
