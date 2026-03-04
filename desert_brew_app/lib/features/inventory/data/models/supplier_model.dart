import '../../domain/entities/supplier.dart';

/// Data model for Supplier — handles JSON serialization.
class SupplierModel extends Supplier {
  const SupplierModel({
    required super.id,
    required super.name,
    super.rfc,
    super.contactName,
    super.phone,
    super.email,
    super.address,
    super.paymentTermsDays,
    super.creditLimit,
    super.isActive,
    super.notes,
  });

  factory SupplierModel.fromJson(Map<String, dynamic> json) {
    final paymentTerms = json['payment_terms'] as String?;
    final paymentTermsDays =
        json['payment_terms_days'] as int? ??
        (paymentTerms != null
            ? int.tryParse(
              RegExp(r'\d+').firstMatch(paymentTerms)?.group(0) ?? '',
            )
            : null);
    return SupplierModel(
      id: json['id'] as int,
      name: json['name'] as String,
      rfc: json['rfc'] as String?,
      contactName:
          (json['contact_person'] as String?) ??
          (json['contact_name'] as String?),
      phone: json['phone'] as String?,
      email: json['email'] as String?,
      address: json['address'] as String?,
      paymentTermsDays: paymentTermsDays,
      creditLimit:
          json['credit_limit'] != null
              ? (json['credit_limit'] as num).toDouble()
              : null,
      isActive: json['is_active'] as bool? ?? true,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    if (rfc != null) 'rfc': rfc,
    if (contactName != null) 'contact_person': contactName,
    if (phone != null) 'phone': phone,
    if (email != null) 'email': email,
    if (address != null) 'address': address,
    if (paymentTermsDays != null) 'payment_terms': '${paymentTermsDays} días',
    if (creditLimit != null) 'credit_limit': creditLimit,
    if (notes != null) 'notes': notes,
  };
}
