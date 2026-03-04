import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/production_repository.dart';
import '../../../domain/entities/production_batch.dart';
import '../../../domain/entities/recipe_stock_validation.dart';
import '../../../domain/entities/style_guidelines.dart';

part 'batch_event.dart';
part 'batch_state.dart';

class BatchBloc extends Bloc<BatchEvent, BatchState> {
  BatchBloc(this._repository) : super(BatchInitial()) {
    on<BatchLoadRequested>(_onLoad);
    on<BatchDetailRequested>(_onDetail);
    on<BatchCreateSubmitted>(_onCreate);
    on<BatchStartBrewingRequested>(_onStartBrewing);
    on<BatchStartFermentingRequested>(_onStartFermenting);
    on<BatchStartConditioningRequested>(_onStartConditioning);
    on<BatchStartPackagingRequested>(_onStartPackaging);
    on<BatchCancelRequested>(_onCancel);
    on<BatchCompleteRequested>(_onComplete);
  }

  final ProductionRepository _repository;

  Future<void> _onLoad(
    BatchLoadRequested event,
    Emitter<BatchState> emit,
  ) async {
    emit(BatchLoading());
    try {
      final batches = await _repository.getBatches(status: event.statusFilter);
      emit(BatchListLoaded(batches));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onDetail(
    BatchDetailRequested event,
    Emitter<BatchState> emit,
  ) async {
    emit(BatchLoading());
    try {
      final batch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(batch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onCreate(
    BatchCreateSubmitted event,
    Emitter<BatchState> emit,
  ) async {
    try {
      final recipe = await _repository.getRecipe(event.recipeId);
      final styleProfile = BeerStyleGuidelines.match(recipe.style);

      if (styleProfile != null) {
        final recipeWaterProfile =
            recipe.waterProfile ?? const <String, dynamic>{};
        final waterNullable = <String, double?>{
          'ca': (recipeWaterProfile['ca'] as num?)?.toDouble(),
          'mg': (recipeWaterProfile['mg'] as num?)?.toDouble(),
          'na': (recipeWaterProfile['na'] as num?)?.toDouble(),
          'cl': (recipeWaterProfile['cl'] as num?)?.toDouble(),
          'so4': (recipeWaterProfile['so4'] as num?)?.toDouble(),
          'hco3': (recipeWaterProfile['hco3'] as num?)?.toDouble(),
        };

        final missing = styleProfile.missingMetrics(
          expectedOg: recipe.expectedOg,
          expectedFg: recipe.expectedFg,
          expectedAbv: recipe.expectedAbv,
          ibu: recipe.ibu,
        );
        if (missing.isNotEmpty) {
          emit(
            BatchError(
              'La receta ${recipe.name} (${styleProfile.name}) requiere '
              'métricas: ${missing.join(', ')}.',
            ),
          );
          return;
        }

        final missingAdvanced = styleProfile.missingAdvancedMetrics(
          colorSrm: recipe.colorSrm,
          waterProfile: waterNullable,
        );
        if (missingAdvanced.isNotEmpty) {
          emit(
            BatchError(
              'La receta ${recipe.name} (${styleProfile.name}) requiere '
              '${missingAdvanced.join(', ')}.',
            ),
          );
          return;
        }

        final targetIssues = styleProfile.validateRecipeTargets(
          expectedOg: recipe.expectedOg!,
          expectedFg: recipe.expectedFg!,
          expectedAbv: recipe.expectedAbv!,
          ibu: recipe.ibu!,
          colorSrm: recipe.colorSrm!,
        );
        if (targetIssues.isNotEmpty) {
          emit(BatchError(targetIssues.first));
          return;
        }

        final waterProfile = <String, double>{
          for (final entry in waterNullable.entries)
            if (entry.value != null) entry.key: entry.value!,
        };
        final waterIssues = styleProfile.validateWaterProfile(waterProfile);
        if (waterIssues.isNotEmpty) {
          emit(BatchError(waterIssues.first));
          return;
        }

        final volumeIssues = styleProfile.validateBatchScale(
          recipeBatchSizeLiters: recipe.batchSizeLiters,
          plannedVolumeLiters: event.plannedVolumeLiters,
        );
        if (volumeIssues.isNotEmpty) {
          emit(BatchError(volumeIssues.first));
          return;
        }
      }

      await _repository.createBatch(
        recipeId: event.recipeId,
        batchNumber: event.batchNumber,
        plannedVolumeLiters: event.plannedVolumeLiters,
        notes: event.notes,
      );
      // Reload list after create
      final batches = await _repository.getBatches();
      emit(BatchListLoaded(batches));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onStartBrewing(
    BatchStartBrewingRequested event,
    Emitter<BatchState> emit,
  ) async {
    try {
      final batch = await _repository.getBatch(event.batchId);
      final validation = await _repository.validateRecipeStock(
        recipeId: batch.recipeId,
        plannedVolumeLiters: batch.plannedVolumeLiters,
      );
      if (!validation.allAvailable) {
        final firstIssue = validation.items.firstWhere(
          (item) => item.status != StockValidationStatus.ok,
          orElse:
              () => const RecipeStockValidationItem(
                ingredientType: 'UNKNOWN',
                name: 'Insumo',
                lookupKey: '',
                requiredQuantity: 0,
                unit: '',
                availableQuantity: 0,
                status: StockValidationStatus.missing,
                matchedBatches: 0,
              ),
        );

        emit(
          BatchError(
            'Stock insuficiente para iniciar lote: ${firstIssue.name} (${firstIssue.status.name.toUpperCase()})',
          ),
        );
        return;
      }

      await _repository.startBrewing(event.batchId);
      final updatedBatch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(updatedBatch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onStartFermenting(
    BatchStartFermentingRequested event,
    Emitter<BatchState> emit,
  ) async {
    try {
      await _repository.startFermenting(event.batchId);
      final batch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(batch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onStartConditioning(
    BatchStartConditioningRequested event,
    Emitter<BatchState> emit,
  ) async {
    try {
      await _repository.startConditioning(event.batchId);
      final batch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(batch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onStartPackaging(
    BatchStartPackagingRequested event,
    Emitter<BatchState> emit,
  ) async {
    try {
      await _repository.startPackaging(event.batchId);
      final batch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(batch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onCancel(
    BatchCancelRequested event,
    Emitter<BatchState> emit,
  ) async {
    try {
      await _repository.cancelBatch(
        batchId: event.batchId,
        reason: event.reason,
      );
      final batch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(batch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }

  Future<void> _onComplete(
    BatchCompleteRequested event,
    Emitter<BatchState> emit,
  ) async {
    try {
      await _repository.completeBatch(
        batchId: event.batchId,
        actualVolumeLiters: event.actualVolumeLiters,
        actualOg: event.actualOg,
        actualFg: event.actualFg,
      );
      final batch = await _repository.getBatch(event.batchId);
      emit(BatchDetailLoaded(batch));
    } catch (e) {
      emit(BatchError(e.toString()));
    }
  }
}
