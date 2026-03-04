part of 'income_bloc.dart';

abstract class IncomeBlocState {}

class IncomeInitial extends IncomeBlocState {}

class IncomeLoading extends IncomeBlocState {}

class IncomeLoaded extends IncomeBlocState {
  IncomeLoaded({required this.incomes, required this.summary});
  final List<IncomeEntry> incomes;
  final IncomeSummary summary;
}

class IncomeError extends IncomeBlocState {
  IncomeError(this.message);
  final String message;
}

class IncomeActionSuccess extends IncomeBlocState {
  IncomeActionSuccess(this.message);
  final String message;
}
