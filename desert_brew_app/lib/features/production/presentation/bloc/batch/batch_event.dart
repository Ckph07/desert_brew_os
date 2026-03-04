part of 'batch_bloc.dart';

abstract class BatchEvent {}

class BatchLoadRequested extends BatchEvent {
  BatchLoadRequested({this.statusFilter});
  final String? statusFilter;
}

class BatchDetailRequested extends BatchEvent {
  BatchDetailRequested(this.batchId);
  final int batchId;
}

class BatchCreateSubmitted extends BatchEvent {
  BatchCreateSubmitted({
    required this.recipeId,
    required this.batchNumber,
    required this.plannedVolumeLiters,
    this.notes,
  });
  final int recipeId;
  final String batchNumber;
  final double plannedVolumeLiters;
  final String? notes;
}

class BatchStartBrewingRequested extends BatchEvent {
  BatchStartBrewingRequested(this.batchId);
  final int batchId;
}

class BatchStartFermentingRequested extends BatchEvent {
  BatchStartFermentingRequested(this.batchId);
  final int batchId;
}

class BatchStartConditioningRequested extends BatchEvent {
  BatchStartConditioningRequested(this.batchId);
  final int batchId;
}

class BatchStartPackagingRequested extends BatchEvent {
  BatchStartPackagingRequested(this.batchId);
  final int batchId;
}

class BatchCancelRequested extends BatchEvent {
  BatchCancelRequested({required this.batchId, this.reason});
  final int batchId;
  final String? reason;
}

class BatchCompleteRequested extends BatchEvent {
  BatchCompleteRequested({
    required this.batchId,
    required this.actualVolumeLiters,
    this.actualOg,
    this.actualFg,
  });
  final int batchId;
  final double actualVolumeLiters;
  final double? actualOg;
  final double? actualFg;
}
