import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/entities/product.dart';
import '../../../domain/repositories/sales_repository.dart';

part 'product_event.dart';
part 'product_state.dart';

class ProductBloc extends Bloc<ProductEvent, ProductState> {
  ProductBloc(this._repository) : super(ProductInitial()) {
    on<ProductLoadRequested>(_onLoad);
    on<MarginReportRequested>(_onMarginReport);
  }

  final SalesRepository _repository;

  Future<void> _onLoad(
      ProductLoadRequested event, Emitter<ProductState> emit) async {
    emit(ProductLoading());
    try {
      final products = await _repository.getProducts(
        activeOnly: event.activeOnly,
        category: event.category,
      );
      emit(ProductLoaded(products, filterCategory: event.category));
    } catch (e) {
      emit(ProductError(e.toString()));
    }
  }

  Future<void> _onMarginReport(
      MarginReportRequested event, Emitter<ProductState> emit) async {
    emit(ProductLoading());
    try {
      final report = await _repository.getMarginReport();
      final items = (report['products'] as List? ?? [])
          .cast<Map<String, dynamic>>()
          .toList();
      emit(MarginReportLoaded(
        items: items,
        avgFixedMargin: (report['avg_fixed_margin'] as num?)?.toDouble(),
        avgTheoreticalMargin:
            (report['avg_theoretical_margin'] as num?)?.toDouble(),
      ));
    } catch (e) {
      emit(ProductError(e.toString()));
    }
  }
}
