part of 'liters_by_style_bloc.dart';
abstract class LitersByStyleState {}
class LitersByStyleInitial extends LitersByStyleState {}
class LitersByStyleLoading extends LitersByStyleState {}
class LitersByStyleLoaded extends LitersByStyleState {
  LitersByStyleLoaded(this.summary);
  final StyleLitersSummary summary;
}
class LitersByStyleError extends LitersByStyleState {
  LitersByStyleError(this.message);
  final String message;
}
