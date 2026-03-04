import '../../domain/entities/product.dart';

class ProductModel extends Product {
  const ProductModel({
    required super.id,
    required super.sku,
    required super.productName,
    required super.category,
    required super.originType,
    required super.unitMeasure,
    required super.isActive,
    super.description,
    super.style,
    super.volumeMl,
    super.abv,
    super.ibu,
    super.fixedPrice,
    super.theoreticalPrice,
    super.costPerUnit,
    super.fixedMarginPct,
    super.theoreticalMarginPct,
    super.priceTaproom,
    super.priceDistributor,
    super.priceOnPremise,
    super.priceOffPremise,
    super.priceEcommerce,
    super.iepsRate,
    super.ivaRate,
    super.notes,
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
    double? _d(String key) =>
        json[key] != null ? (json[key] as num).toDouble() : null;

    return ProductModel(
      id: json['id'] as int,
      sku: json['sku'] as String,
      productName: json['product_name'] as String,
      category: json['category'] as String,
      originType: json['origin_type'] as String,
      unitMeasure: json['unit_measure'] as String,
      isActive: json['is_active'] as bool? ?? true,
      description: json['description'] as String?,
      style: json['style'] as String?,
      volumeMl: json['volume_ml'] as int?,
      abv: _d('abv'),
      ibu: json['ibu'] as int?,
      fixedPrice: _d('fixed_price'),
      theoreticalPrice: _d('theoretical_price'),
      costPerUnit: _d('cost_per_unit'),
      fixedMarginPct: _d('fixed_margin_pct'),
      theoreticalMarginPct: _d('theoretical_margin_pct'),
      priceTaproom: _d('price_taproom'),
      priceDistributor: _d('price_distributor'),
      priceOnPremise: _d('price_on_premise'),
      priceOffPremise: _d('price_off_premise'),
      priceEcommerce: _d('price_ecommerce'),
      iepsRate: _d('ieps_rate'),
      ivaRate: _d('iva_rate'),
      notes: json['notes'] as String?,
    );
  }
}
