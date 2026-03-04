part of 'expense_bloc.dart';

abstract class ExpenseBlocState {}

class ExpenseInitial extends ExpenseBlocState {}

class ExpenseLoading extends ExpenseBlocState {}

class ExpenseLoaded extends ExpenseBlocState {
  ExpenseLoaded({required this.expenses, required this.summary});
  final List<ExpenseEntry> expenses;
  final ExpenseSummary summary;
}

class ExpenseError extends ExpenseBlocState {
  ExpenseError(this.message);
  final String message;
}

class ExpenseActionSuccess extends ExpenseBlocState {
  ExpenseActionSuccess(this.message);
  final String message;
}
