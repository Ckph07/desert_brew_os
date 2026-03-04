part of 'supplier_bloc.dart';

abstract class SupplierEvent {}

class SupplierLoadRequested extends SupplierEvent {
  SupplierLoadRequested({this.activeOnly = true});
  final bool activeOnly;
}

class SupplierCreateSubmitted extends SupplierEvent {
  SupplierCreateSubmitted({
    required this.name,
    this.rfc,
    this.contactName,
    this.phone,
    this.email,
    this.paymentTermsDays,
    this.creditLimit,
  });
  final String name;
  final String? rfc;
  final String? contactName;
  final String? phone;
  final String? email;
  final int? paymentTermsDays;
  final double? creditLimit;
}
