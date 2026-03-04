part of 'finished_product_bloc.dart';
abstract class FinishedProductState {}
class FinishedProductInitial extends FinishedProductState {}
class FinishedProductLoading extends FinishedProductState {}
class FinishedProductLoaded extends FinishedProductState {
  FinishedProductLoaded({
    required this.products,
    required this.summary,
    required this.coldRooms,
  });
  final List<FinishedProduct> products;
  final Map<String, dynamic> summary;
  final List<ColdRoomStatus> coldRooms;
}
class FinishedProductError extends FinishedProductState {
  FinishedProductError(this.message);
  final String message;
}
