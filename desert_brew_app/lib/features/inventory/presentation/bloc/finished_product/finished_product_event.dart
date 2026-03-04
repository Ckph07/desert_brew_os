part of 'finished_product_bloc.dart';
abstract class FinishedProductEvent {}

class FinishedProductLoadRequested extends FinishedProductEvent {
  FinishedProductLoadRequested({this.productTypeFilter, this.coldRoomFilter});
  final String? productTypeFilter;
  final String? coldRoomFilter;
}
