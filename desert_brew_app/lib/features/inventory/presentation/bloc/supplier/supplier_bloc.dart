import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/entities/supplier.dart';
import '../../../domain/repositories/inventory_repository.dart';

part 'supplier_event.dart';
part 'supplier_state.dart';

class SupplierBloc extends Bloc<SupplierEvent, SupplierState> {
  SupplierBloc(this._repository) : super(SupplierInitial()) {
    on<SupplierLoadRequested>(_onLoad);
    on<SupplierCreateSubmitted>(_onCreate);
  }

  final InventoryRepository _repository;

  Future<void> _onLoad(
      SupplierLoadRequested event, Emitter<SupplierState> emit) async {
    emit(SupplierLoading());
    try {
      final suppliers =
          await _repository.getSuppliers(activeOnly: event.activeOnly);
      emit(SupplierLoaded(suppliers));
    } catch (e) {
      emit(SupplierError(e.toString()));
    }
  }

  Future<void> _onCreate(
      SupplierCreateSubmitted event, Emitter<SupplierState> emit) async {
    try {
      final supplier = await _repository.createSupplier(
        name: event.name,
        rfc: event.rfc,
        contactName: event.contactName,
        phone: event.phone,
        email: event.email,
        paymentTermsDays: event.paymentTermsDays,
        creditLimit: event.creditLimit,
      );
      emit(SupplierCreateSuccess(supplier));
      add(SupplierLoadRequested());
    } catch (e) {
      emit(SupplierError(e.toString()));
    }
  }
}
