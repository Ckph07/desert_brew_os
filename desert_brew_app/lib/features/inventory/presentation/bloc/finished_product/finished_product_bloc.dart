import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/repositories/inventory_repository.dart';
import '../../../domain/entities/finished_product.dart';

part 'finished_product_event.dart';
part 'finished_product_state.dart';

class FinishedProductBloc extends Bloc<FinishedProductEvent, FinishedProductState> {
  FinishedProductBloc(this._repo) : super(FinishedProductInitial()) {
    on<FinishedProductLoadRequested>(_onLoad);
  }

  final InventoryRepository _repo;

  Future<void> _onLoad(
      FinishedProductLoadRequested event, Emitter<FinishedProductState> emit) async {
    emit(FinishedProductLoading());
    try {
      final results = await Future.wait([
        _repo.getFinishedProducts(
          productType: event.productTypeFilter,
          coldRoomId: event.coldRoomFilter,
        ),
        _repo.getFinishedProductSummary(),
        _repo.getColdRoomStatus(),
      ]);
      emit(FinishedProductLoaded(
        products: results[0] as List<FinishedProduct>,
        summary: results[1] as Map<String, dynamic>,
        coldRooms: results[2] as List<ColdRoomStatus>,
      ));
    } catch (e) {
      emit(FinishedProductError(e.toString()));
    }
  }
}
