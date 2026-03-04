part of 'client_bloc.dart';
abstract class ClientState {}
class ClientInitial extends ClientState {}
class ClientLoading extends ClientState {}
class ClientLoaded extends ClientState {
  ClientLoaded(this.clients);
  final List<SalesClient> clients;
}
class ClientError extends ClientState {
  ClientError(this.message);
  final String message;
}
