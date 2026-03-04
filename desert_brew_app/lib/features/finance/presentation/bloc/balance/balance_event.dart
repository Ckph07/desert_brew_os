part of 'balance_bloc.dart';
abstract class BalanceEvent {}
class BalanceLoadRequested extends BalanceEvent {
  BalanceLoadRequested({this.days = 30, this.months = 6});
  final int days;
  final int months;
}
