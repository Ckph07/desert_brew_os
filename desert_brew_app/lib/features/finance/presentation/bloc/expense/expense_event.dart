part of 'expense_bloc.dart';

abstract class ExpenseEvent {}

class ExpenseLoadRequested extends ExpenseEvent {
  ExpenseLoadRequested({this.category, this.profitCenter, this.days});
  final String? category;
  final String? profitCenter;
  final int? days;
}

class ExpenseCreateRequested extends ExpenseEvent {
  ExpenseCreateRequested(this.payload);
  final Map<String, dynamic> payload;
}

class ExpenseUpdateRequested extends ExpenseEvent {
  ExpenseUpdateRequested({required this.id, required this.payload});
  final int id;
  final Map<String, dynamic> payload;
}

class ExpenseDeleteRequested extends ExpenseEvent {
  ExpenseDeleteRequested(this.id);
  final int id;
}
