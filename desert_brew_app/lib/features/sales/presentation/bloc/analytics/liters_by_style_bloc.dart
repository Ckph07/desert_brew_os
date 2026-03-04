import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/entities/style_liters_summary.dart';
import '../../../domain/repositories/sales_repository.dart';

part 'liters_by_style_event.dart';
part 'liters_by_style_state.dart';

class LitersByStyleBloc
    extends Bloc<LitersByStyleEvent, LitersByStyleState> {
  LitersByStyleBloc(this._repository) : super(LitersByStyleInitial()) {
    on<LitersByStyleLoadRequested>(_onLoad);
  }

  final SalesRepository _repository;

  Future<void> _onLoad(
      LitersByStyleLoadRequested event,
      Emitter<LitersByStyleState> emit) async {
    emit(LitersByStyleLoading());
    try {
      final summary = await _repository.getLitersByStyle(
        since: event.since,
        until: event.until,
        channel: event.channel,
      );
      emit(LitersByStyleLoaded(summary));
    } catch (e) {
      emit(LitersByStyleError(e.toString()));
    }
  }
}
