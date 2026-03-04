part of 'recipe_bloc.dart';
abstract class RecipeState {}
class RecipeInitial extends RecipeState {}
class RecipeLoading extends RecipeState {}
class RecipeLoaded extends RecipeState {
  RecipeLoaded(this.recipes);
  final List<Recipe> recipes;
}
class RecipeError extends RecipeState {
  RecipeError(this.message);
  final String message;
}
