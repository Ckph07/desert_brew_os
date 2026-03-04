import 'package:equatable/equatable.dart';

/// Sales note line item.
class SalesNoteItem extends Equatable {
  const SalesNoteItem({
    required this.id,
    required this.productName,
    required this.unitMeasure,
    required this.quantity,
    required this.unitPrice,
    required this.discountPct,
    required this.subtotal,
    required this.iepsAmount,
    required this.ivaAmount,
    required this.lineTotal,
    this.productId,
    this.sku,
  });

  final int id;
  final String productName;
  final String unitMeasure;
  final double quantity;
  final double unitPrice;
  final double discountPct;
  final double subtotal;
  final double iepsAmount;
  final double ivaAmount;
  final double lineTotal;
  final int? productId;
  final String? sku;

  @override
  List<Object?> get props => [id, productName, quantity, unitPrice];
}

/// Sales note entity — the core commercial document.
/// status: DRAFT | CONFIRMED | CANCELLED
/// payment_status: PENDING | PAID | PARTIAL | OVERDUE
class SalesNote extends Equatable {
  const SalesNote({
    required this.id,
    required this.noteNumber,
    required this.issuerName,
    required this.issuerRfc,
    required this.includeTaxes,
    required this.subtotal,
    required this.iepsTotal,
    required this.ivaTotal,
    required this.total,
    required this.totalLiters,
    required this.channel,
    required this.paymentMethod,
    required this.paymentStatus,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    required this.items,
    this.clientId,
    this.clientName,
    this.notes,
    this.createdBy,
    this.confirmedAt,
  });

  final int id;
  final String noteNumber;
  final String issuerName;
  final String issuerRfc;
  final bool includeTaxes;
  final double subtotal;
  final double iepsTotal;
  final double ivaTotal;
  final double total;
  final double totalLiters;
  final String channel;
  final String paymentMethod;
  final String paymentStatus;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<SalesNoteItem> items;
  final int? clientId;
  final String? clientName;
  final String? notes;
  final String? createdBy;
  final DateTime? confirmedAt;

  bool get isDraft => status == 'DRAFT';
  bool get isConfirmed => status == 'CONFIRMED';
  bool get isPaid => paymentStatus == 'PAID';

  @override
  List<Object?> get props => [id, noteNumber, status, paymentStatus, total];
}
