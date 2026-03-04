part of 'income_bloc.dart';

abstract class IncomeEvent {}

class IncomeLoadRequested extends IncomeEvent {
  IncomeLoadRequested({this.category, this.profitCenter, this.days});
  final String? category;
  final String? profitCenter;
  final int? days;
}

class IncomeCreateRequested extends IncomeEvent {
  IncomeCreateRequested(this.payload);
  final Map<String, dynamic> payload;
}

class IncomeUpdateRequested extends IncomeEvent {
  IncomeUpdateRequested({required this.id, required this.payload});
  final int id;
  final Map<String, dynamic> payload;
}

class IncomeDeleteRequested extends IncomeEvent {
  IncomeDeleteRequested(this.id);
  final int id;
}
