part of 'supplier_bloc.dart';

abstract class SupplierState {}

class SupplierInitial extends SupplierState {}
class SupplierLoading extends SupplierState {}

class SupplierLoaded extends SupplierState {
  SupplierLoaded(this.suppliers);
  final List<Supplier> suppliers;
}

class SupplierError extends SupplierState {
  SupplierError(this.message);
  final String message;
}

class SupplierCreateSuccess extends SupplierState {
  SupplierCreateSuccess(this.supplier);
  final Supplier supplier;
}
