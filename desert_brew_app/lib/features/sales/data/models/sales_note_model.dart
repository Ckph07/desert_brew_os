import '../../domain/entities/sales_note.dart';

class SalesNoteItemModel extends SalesNoteItem {
  const SalesNoteItemModel({
    required super.id,
    required super.productName,
    required super.unitMeasure,
    required super.quantity,
    required super.unitPrice,
    required super.discountPct,
    required super.subtotal,
    required super.iepsAmount,
    required super.ivaAmount,
    required super.lineTotal,
    super.productId,
    super.sku,
  });

  factory SalesNoteItemModel.fromJson(Map<String, dynamic> json) {
    return SalesNoteItemModel(
      id: json['id'] as int,
      productName: json['product_name'] as String,
      unitMeasure: json['unit_measure'] as String,
      quantity: (json['quantity'] as num).toDouble(),
      unitPrice: (json['unit_price'] as num).toDouble(),
      discountPct: (json['discount_pct'] as num).toDouble(),
      subtotal: (json['subtotal'] as num).toDouble(),
      iepsAmount: (json['ieps_amount'] as num).toDouble(),
      ivaAmount: (json['iva_amount'] as num).toDouble(),
      lineTotal: (json['line_total'] as num).toDouble(),
      productId: json['product_id'] as int?,
      sku: json['sku'] as String?,
    );
  }
}

class SalesNoteModel extends SalesNote {
  const SalesNoteModel({
    required super.id,
    required super.noteNumber,
    required super.issuerName,
    required super.issuerRfc,
    required super.includeTaxes,
    required super.includeIeps,
    required super.includeIva,
    required super.subtotal,
    required super.iepsTotal,
    required super.ivaTotal,
    required super.total,
    required super.totalLiters,
    required super.channel,
    required super.paymentMethod,
    required super.paymentStatus,
    required super.status,
    required super.createdAt,
    required super.updatedAt,
    required super.items,
    super.clientId,
    super.clientName,
    super.notes,
    super.createdBy,
    super.confirmedAt,
  });

  factory SalesNoteModel.fromJson(Map<String, dynamic> json) {
    final itemsList =
        (json['items'] as List<dynamic>? ?? [])
            .map((e) => SalesNoteItemModel.fromJson(e as Map<String, dynamic>))
            .toList();

    return SalesNoteModel(
      id: json['id'] as int,
      noteNumber: json['note_number'] as String,
      issuerName: json['issuer_name'] as String,
      issuerRfc: json['issuer_rfc'] as String,
      includeTaxes: json['include_taxes'] as bool? ?? false,
      includeIeps:
          json['include_ieps'] as bool? ??
          (json['include_taxes'] as bool? ?? false),
      includeIva:
          json['include_iva'] as bool? ??
          (json['include_taxes'] as bool? ?? false),
      subtotal: (json['subtotal'] as num).toDouble(),
      iepsTotal: (json['ieps_total'] as num).toDouble(),
      ivaTotal: (json['iva_total'] as num).toDouble(),
      total: (json['total'] as num).toDouble(),
      totalLiters: (json['total_liters'] as num).toDouble(),
      channel: json['channel'] as String,
      paymentMethod: json['payment_method'] as String,
      paymentStatus: json['payment_status'] as String,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      items: itemsList,
      clientId: json['client_id'] as int?,
      clientName: json['client_name'] as String?,
      notes: json['notes'] as String?,
      createdBy: json['created_by'] as String?,
      confirmedAt:
          json['confirmed_at'] != null
              ? DateTime.parse(json['confirmed_at'] as String)
              : null,
    );
  }
}
