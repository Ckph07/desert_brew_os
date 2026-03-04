import 'package:equatable/equatable.dart';

/// Supplier domain entity.
class Supplier extends Equatable {
  const Supplier({
    required this.id,
    required this.name,
    this.rfc,
    this.contactName,
    this.phone,
    this.email,
    this.address,
    this.paymentTermsDays,
    this.creditLimit,
    this.isActive = true,
    this.notes,
  });

  final int id;
  final String name;
  final String? rfc;
  final String? contactName;
  final String? phone;
  final String? email;
  final String? address;
  final int? paymentTermsDays;
  final double? creditLimit;
  final bool isActive;
  final String? notes;

  @override
  List<Object?> get props => [id, name, rfc, isActive];
}
