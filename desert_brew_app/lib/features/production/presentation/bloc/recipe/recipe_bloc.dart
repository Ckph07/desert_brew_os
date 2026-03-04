import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/production_repository.dart';
import '../../../domain/entities/recipe.dart';

part 'recipe_event.dart';
part 'recipe_state.dart';

class RecipeBloc extends Bloc<RecipeEvent, RecipeState> {
  RecipeBloc(this._repository) : super(RecipeInitial()) {
    on<RecipeLoadRequested>(_onLoad);
  }

  final ProductionRepository _repository;

  Future<void> _onLoad(
      RecipeLoadRequested event, Emitter<RecipeState> emit) async {
    emit(RecipeLoading());
    try {
      final recipes = await _repository.getRecipes();
      emit(RecipeLoaded(recipes));
    } catch (e) {
      emit(RecipeError(e.toString()));
    }
  }
}
