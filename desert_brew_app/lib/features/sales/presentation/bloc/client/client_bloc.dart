import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/entities/sales_client.dart';
import '../../../domain/repositories/sales_repository.dart';

part 'client_event.dart';
part 'client_state.dart';

class ClientBloc extends Bloc<ClientEvent, ClientState> {
  ClientBloc(this._repository) : super(ClientInitial()) {
    on<ClientLoadRequested>(_onLoad);
    on<ClientCreateSubmitted>(_onCreate);
  }

  final SalesRepository _repository;

  Future<void> _onLoad(
      ClientLoadRequested event, Emitter<ClientState> emit) async {
    emit(ClientLoading());
    try {
      final clients = await _repository.getClients(
        activeOnly: event.activeOnly,
        search: event.search,
      );
      emit(ClientLoaded(clients));
    } catch (e) {
      emit(ClientError(e.toString()));
    }
  }

  Future<void> _onCreate(
      ClientCreateSubmitted event, Emitter<ClientState> emit) async {
    try {
      await _repository.createClient(
        businessName: event.businessName,
        clientType: event.clientType,
        pricingTier: event.pricingTier,
        legalName: event.legalName,
        rfc: event.rfc,
        email: event.email,
        phone: event.phone,
        city: event.city,
        contactPerson: event.contactPerson,
        creditLimit: event.creditLimit,
        maxKegs: event.maxKegs,
      );
      add(ClientLoadRequested());
    } catch (e) {
      emit(ClientError(e.toString()));
    }
  }
}
