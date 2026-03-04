import 'package:equatable/equatable.dart';

/// Client domain entity.
/// client_type: B2B | B2C | DISTRIBUTOR
/// pricing_tier: PLATINUM | GOLD | SILVER | RETAIL
class SalesClient extends Equatable {
  const SalesClient({
    required this.id,
    required this.clientCode,
    required this.businessName,
    required this.clientType,
    required this.pricingTier,
    required this.currentBalance,
    required this.currentKegs,
    required this.isActive,
    this.legalName,
    this.rfc,
    this.email,
    this.phone,
    this.address,
    this.city,
    this.state,
    this.contactPerson,
    this.creditLimit,
    this.maxKegs,
    this.notes,
    this.createdAt,
  });

  final int id;
  final String clientCode;
  final String businessName;
  final String clientType;
  final String pricingTier;
  final double currentBalance;
  final int currentKegs;
  final bool isActive;
  final String? legalName;
  final String? rfc;
  final String? email;
  final String? phone;
  final String? address;
  final String? city;
  final String? state;
  final String? contactPerson;
  final double? creditLimit;
  final int? maxKegs;
  final String? notes;
  final DateTime? createdAt;

  double get availableCredit =>
      (creditLimit ?? double.infinity) - currentBalance;
  bool get hasCredit =>
      creditLimit == null || currentBalance < creditLimit!;
  int get availableKegs => (maxKegs ?? 999) - currentKegs;

  @override
  List<Object?> get props =>
      [id, clientCode, businessName, clientType, pricingTier, isActive];
}
