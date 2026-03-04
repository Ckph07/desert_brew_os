import 'package:equatable/equatable.dart';

/// Product catalog entity with dual pricing and channel prices.
class Product extends Equatable {
  const Product({
    required this.id,
    required this.sku,
    required this.productName,
    required this.category,
    required this.originType,
    required this.unitMeasure,
    required this.isActive,
    this.description,
    this.style,
    this.volumeMl,
    this.abv,
    this.ibu,
    this.fixedPrice,
    this.theoreticalPrice,
    this.costPerUnit,
    this.fixedMarginPct,
    this.theoreticalMarginPct,
    this.priceTaproom,
    this.priceDistributor,
    this.priceOnPremise,
    this.priceOffPremise,
    this.priceEcommerce,
    this.iepsRate,
    this.ivaRate,
    this.notes,
  });

  final int id;
  final String sku;
  final String productName;
  final String category;
  final String originType; // HOUSE | GUEST | COMMERCIAL
  final String unitMeasure;
  final bool isActive;
  final String? description;
  final String? style;
  final int? volumeMl;
  final double? abv;
  final int? ibu;
  // Dual pricing
  final double? fixedPrice;
  final double? theoreticalPrice;
  final double? costPerUnit;
  final double? fixedMarginPct;
  final double? theoreticalMarginPct;
  // Channel pricing
  final double? priceTaproom;
  final double? priceDistributor;
  final double? priceOnPremise;
  final double? priceOffPremise;
  final double? priceEcommerce;
  // Tax
  final double? iepsRate;
  final double? ivaRate;
  final String? notes;

  bool get isHouse => originType == 'HOUSE';
  double get displayPrice => fixedPrice ?? theoreticalPrice ?? 0;

  @override
  List<Object?> get props => [id, sku, productName, category, isActive];
}
