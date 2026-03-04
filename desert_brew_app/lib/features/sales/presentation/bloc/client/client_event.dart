part of 'client_bloc.dart';
abstract class ClientEvent {}
class ClientLoadRequested extends ClientEvent {
  ClientLoadRequested({this.activeOnly = true, this.search});
  final bool activeOnly;
  final String? search;
}
class ClientCreateSubmitted extends ClientEvent {
  ClientCreateSubmitted({
    required this.businessName,
    required this.clientType,
    required this.pricingTier,
    this.legalName,
    this.rfc,
    this.email,
    this.phone,
    this.city,
    this.contactPerson,
    this.creditLimit,
    this.maxKegs,
  });
  final String businessName;
  final String clientType;
  final String pricingTier;
  final String? legalName;
  final String? rfc;
  final String? email;
  final String? phone;
  final String? city;
  final String? contactPerson;
  final double? creditLimit;
  final int? maxKegs;
}
