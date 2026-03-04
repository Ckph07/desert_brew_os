import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/inventory_repository.dart';
import '../../../domain/entities/keg_asset.dart';

part 'keg_event.dart';
part 'keg_state.dart';

class KegBloc extends Bloc<KegEvent, KegBlocState> {
  KegBloc(this._repo) : super(KegInitial()) {
    on<KegLoadRequested>(_onLoad);
    on<KegTransitionRequested>(_onTransition);
  }

  final InventoryRepository _repo;

  Future<void> _onLoad(KegLoadRequested event, Emitter<KegBlocState> emit) async {
    emit(KegLoading());
    try {
      final kegs = await _repo.getKegs(state: event.stateFilter);
      emit(KegLoaded(kegs));
    } catch (e) {
      emit(KegError(e.toString()));
    }
  }

  Future<void> _onTransition(
      KegTransitionRequested event, Emitter<KegBlocState> emit) async {
    try {
      await _repo.transitionKeg(
        kegId: event.kegId,
        newState: event.newState,
        userId: event.userId,
        location: event.location,
        reason: event.reason,
      );
      // Reload after transition
      final kegs = await _repo.getKegs();
      emit(KegLoaded(kegs));
    } catch (e) {
      emit(KegError(e.toString()));
    }
  }
}
