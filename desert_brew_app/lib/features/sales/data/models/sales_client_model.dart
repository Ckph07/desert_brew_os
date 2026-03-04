import '../../domain/entities/sales_client.dart';

class SalesClientModel extends SalesClient {
  const SalesClientModel({
    required super.id,
    required super.clientCode,
    required super.businessName,
    required super.clientType,
    required super.pricingTier,
    required super.currentBalance,
    required super.currentKegs,
    required super.isActive,
    super.legalName,
    super.rfc,
    super.email,
    super.phone,
    super.address,
    super.city,
    super.state,
    super.contactPerson,
    super.creditLimit,
    super.maxKegs,
    super.notes,
    super.createdAt,
  });

  factory SalesClientModel.fromJson(Map<String, dynamic> json) {
    return SalesClientModel(
      id: json['id'] as int,
      clientCode: json['client_code'] as String,
      businessName: json['business_name'] as String,
      clientType: json['client_type'] as String,
      pricingTier: json['pricing_tier'] as String,
      currentBalance: (json['current_balance'] as num).toDouble(),
      currentKegs: (json['current_kegs'] as num).toInt(),
      isActive: json['is_active'] as bool? ?? true,
      legalName: json['legal_name'] as String?,
      rfc: json['rfc'] as String?,
      email: json['email'] as String?,
      phone: json['phone'] as String?,
      address: json['address'] as String?,
      city: json['city'] as String?,
      state: json['state'] as String?,
      contactPerson: json['contact_person'] as String?,
      creditLimit: json['credit_limit'] != null
          ? (json['credit_limit'] as num).toDouble()
          : null,
      maxKegs: json['max_kegs'] as int?,
      notes: json['notes'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'business_name': businessName,
        'client_type': clientType,
        'pricing_tier': pricingTier,
        if (legalName != null) 'legal_name': legalName,
        if (rfc != null) 'rfc': rfc,
        if (email != null) 'email': email,
        if (phone != null) 'phone': phone,
        if (address != null) 'address': address,
        if (city != null) 'city': city,
        if (contactPerson != null) 'contact_person': contactPerson,
        if (creditLimit != null) 'credit_limit': creditLimit,
        if (maxKegs != null) 'max_kegs': maxKegs,
        if (notes != null) 'notes': notes,
      };
}
