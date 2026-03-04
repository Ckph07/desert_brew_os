import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/production_repository.dart';
import '../../../domain/entities/cost_entities.dart';

part 'costs_event.dart';
part 'costs_state.dart';

class CostsBloc extends Bloc<CostsEvent, CostsState> {
  CostsBloc(this._repository) : super(CostsInitial()) {
    on<CostsLoadRequested>(_onLoad);
  }

  final ProductionRepository _repository;

  Future<void> _onLoad(
      CostsLoadRequested event, Emitter<CostsState> emit) async {
    emit(CostsLoading());
    try {
      final results = await Future.wait([
        _repository.getCostSummary(),
        _repository.getFixedCosts(),
        _repository.getIngredientPrices(),
      ]);
      emit(CostsLoaded(
        summary: results[0] as CostSummary,
        fixedCosts: results[1] as List<FixedMonthlyCost>,
        ingredientPrices: results[2] as List<IngredientPrice>,
      ));
    } catch (e) {
      emit(CostsError(e.toString()));
    }
  }
}
