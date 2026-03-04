import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/finance_repository.dart';
import '../../../domain/entities/balance.dart';

part 'balance_event.dart';
part 'balance_state.dart';

class BalanceBloc extends Bloc<BalanceEvent, BalanceBlocState> {
  BalanceBloc(this._repo) : super(BalanceInitial()) {
    on<BalanceLoadRequested>(_onLoad);
  }
  final FinanceRepository _repo;

  Future<void> _onLoad(BalanceLoadRequested e, Emitter<BalanceBlocState> emit) async {
    emit(BalanceLoading());
    try {
      final results = await Future.wait([
        _repo.getBalance(days: e.days),
        _repo.getCashflow(months: e.months),
      ]);
      emit(BalanceLoaded(
        balance: results[0] as BalanceSummary,
        cashflow: results[1] as CashflowReport,
      ));
    } catch (err) {
      emit(BalanceError(err.toString()));
    }
  }
}
