import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/finance_repository.dart';
import '../../../domain/entities/expense_entry.dart';

part 'expense_event.dart';
part 'expense_state.dart';

class ExpenseBloc extends Bloc<ExpenseEvent, ExpenseBlocState> {
  ExpenseBloc(this._repo) : super(ExpenseInitial()) {
    on<ExpenseLoadRequested>(_onLoad);
    on<ExpenseCreateRequested>(_onCreate);
    on<ExpenseUpdateRequested>(_onUpdate);
    on<ExpenseDeleteRequested>(_onDelete);
  }
  final FinanceRepository _repo;
  String? _currentCategory;
  String? _currentProfitCenter;
  int? _currentDays;

  Future<void> _onLoad(
    ExpenseLoadRequested e,
    Emitter<ExpenseBlocState> emit,
  ) async {
    emit(ExpenseLoading());
    try {
      _currentCategory = e.category;
      _currentProfitCenter = e.profitCenter;
      _currentDays = e.days;
      final results = await Future.wait([
        _repo.getExpenses(
          category: e.category,
          profitCenter: e.profitCenter,
          days: e.days,
        ),
        _repo.getExpenseSummary(days: e.days ?? 30),
      ]);
      emit(
        ExpenseLoaded(
          expenses: results[0] as List<ExpenseEntry>,
          summary: results[1] as ExpenseSummary,
        ),
      );
    } catch (err) {
      emit(ExpenseError(err.toString()));
    }
  }

  Future<void> _onCreate(
    ExpenseCreateRequested e,
    Emitter<ExpenseBlocState> emit,
  ) async {
    try {
      await _repo.createExpense(e.payload);
      emit(ExpenseActionSuccess('Egreso creado'));
      add(
        ExpenseLoadRequested(
          category: _currentCategory,
          profitCenter: _currentProfitCenter,
          days: _currentDays,
        ),
      );
    } catch (err) {
      emit(ExpenseError(err.toString()));
    }
  }

  Future<void> _onUpdate(
    ExpenseUpdateRequested e,
    Emitter<ExpenseBlocState> emit,
  ) async {
    try {
      await _repo.updateExpense(e.id, e.payload);
      emit(ExpenseActionSuccess('Egreso actualizado'));
      add(
        ExpenseLoadRequested(
          category: _currentCategory,
          profitCenter: _currentProfitCenter,
          days: _currentDays,
        ),
      );
    } catch (err) {
      emit(ExpenseError(err.toString()));
    }
  }

  Future<void> _onDelete(
    ExpenseDeleteRequested e,
    Emitter<ExpenseBlocState> emit,
  ) async {
    try {
      await _repo.deleteExpense(e.id);
      emit(ExpenseActionSuccess('Egreso eliminado'));
      add(
        ExpenseLoadRequested(
          category: _currentCategory,
          profitCenter: _currentProfitCenter,
          days: _currentDays,
        ),
      );
    } catch (err) {
      emit(ExpenseError(err.toString()));
    }
  }
}
