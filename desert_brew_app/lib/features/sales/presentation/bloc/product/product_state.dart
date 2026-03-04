part of 'product_bloc.dart';
abstract class ProductState {}
class ProductInitial extends ProductState {}
class ProductLoading extends ProductState {}
class ProductLoaded extends ProductState {
  ProductLoaded(this.products, {this.filterCategory});
  final List<Product> products;
  final String? filterCategory;
}
class MarginReportLoaded extends ProductState {
  MarginReportLoaded({
    required this.items,
    this.avgFixedMargin,
    this.avgTheoreticalMargin,
  });
  final List<Map<String, dynamic>> items;
  final double? avgFixedMargin;
  final double? avgTheoreticalMargin;
}
class ProductError extends ProductState {
  ProductError(this.message);
  final String message;
}
