import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/finance_repository.dart';
import '../../../domain/entities/income_entry.dart';

part 'income_event.dart';
part 'income_state.dart';

class IncomeBloc extends Bloc<IncomeEvent, IncomeBlocState> {
  IncomeBloc(this._repo) : super(IncomeInitial()) {
    on<IncomeLoadRequested>(_onLoad);
    on<IncomeCreateRequested>(_onCreate);
    on<IncomeUpdateRequested>(_onUpdate);
    on<IncomeDeleteRequested>(_onDelete);
  }
  final FinanceRepository _repo;
  String? _currentCategory;
  String? _currentProfitCenter;
  int? _currentDays;

  Future<void> _onLoad(
    IncomeLoadRequested e,
    Emitter<IncomeBlocState> emit,
  ) async {
    emit(IncomeLoading());
    try {
      _currentCategory = e.category;
      _currentProfitCenter = e.profitCenter;
      _currentDays = e.days;
      final results = await Future.wait([
        _repo.getIncomes(
          category: e.category,
          profitCenter: e.profitCenter,
          days: e.days,
        ),
        _repo.getIncomeSummary(days: e.days ?? 30),
      ]);
      emit(
        IncomeLoaded(
          incomes: results[0] as List<IncomeEntry>,
          summary: results[1] as IncomeSummary,
        ),
      );
    } catch (err) {
      emit(IncomeError(err.toString()));
    }
  }

  Future<void> _onCreate(
    IncomeCreateRequested e,
    Emitter<IncomeBlocState> emit,
  ) async {
    try {
      await _repo.createIncome(e.payload);
      emit(IncomeActionSuccess('Ingreso creado'));
      add(
        IncomeLoadRequested(
          category: _currentCategory,
          profitCenter: _currentProfitCenter,
          days: _currentDays,
        ),
      );
    } catch (err) {
      emit(IncomeError(err.toString()));
    }
  }

  Future<void> _onUpdate(
    IncomeUpdateRequested e,
    Emitter<IncomeBlocState> emit,
  ) async {
    try {
      await _repo.updateIncome(e.id, e.payload);
      emit(IncomeActionSuccess('Ingreso actualizado'));
      add(
        IncomeLoadRequested(
          category: _currentCategory,
          profitCenter: _currentProfitCenter,
          days: _currentDays,
        ),
      );
    } catch (err) {
      emit(IncomeError(err.toString()));
    }
  }

  Future<void> _onDelete(
    IncomeDeleteRequested e,
    Emitter<IncomeBlocState> emit,
  ) async {
    try {
      await _repo.deleteIncome(e.id);
      emit(IncomeActionSuccess('Ingreso eliminado'));
      add(
        IncomeLoadRequested(
          category: _currentCategory,
          profitCenter: _currentProfitCenter,
          days: _currentDays,
        ),
      );
    } catch (err) {
      emit(IncomeError(err.toString()));
    }
  }
}
