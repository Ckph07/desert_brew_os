part of 'costs_bloc.dart';
abstract class CostsState {}
class CostsInitial extends CostsState {}
class CostsLoading extends CostsState {}
class CostsLoaded extends CostsState {
  CostsLoaded({
    required this.summary,
    required this.fixedCosts,
    required this.ingredientPrices,
  });
  final CostSummary summary;
  final List<FixedMonthlyCost> fixedCosts;
  final List<IngredientPrice> ingredientPrices;
}
class CostsError extends CostsState {
  CostsError(this.message);
  final String message;
}
