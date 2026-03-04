part of 'batch_bloc.dart';
abstract class BatchState {}

class BatchInitial extends BatchState {}
class BatchLoading extends BatchState {}

class BatchListLoaded extends BatchState {
  BatchListLoaded(this.batches);
  final List<ProductionBatch> batches;
}

class BatchDetailLoaded extends BatchState {
  BatchDetailLoaded(this.batch);
  final ProductionBatch batch;
}

class BatchError extends BatchState {
  BatchError(this.message);
  final String message;
}
