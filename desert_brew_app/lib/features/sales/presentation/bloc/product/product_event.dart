part of 'product_bloc.dart';
abstract class ProductEvent {}
class ProductLoadRequested extends ProductEvent {
  ProductLoadRequested({this.activeOnly = true, this.category});
  final bool activeOnly;
  final String? category;
}
class MarginReportRequested extends ProductEvent {}
