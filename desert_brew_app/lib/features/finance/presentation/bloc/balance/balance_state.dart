part of 'balance_bloc.dart';
abstract class BalanceBlocState {}
class BalanceInitial extends BalanceBlocState {}
class BalanceLoading extends BalanceBlocState {}
class BalanceLoaded extends BalanceBlocState {
  BalanceLoaded({required this.balance, required this.cashflow});
  final BalanceSummary balance;
  final CashflowReport cashflow;
}
class BalanceError extends BalanceBlocState {
  BalanceError(this.message);
  final String message;
}
