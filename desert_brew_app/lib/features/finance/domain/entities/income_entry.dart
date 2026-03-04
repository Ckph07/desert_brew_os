import 'package:equatable/equatable.dart';

/// Income categories from backend.
enum IncomeCategory {
  beerSales, merchSales, foodSales, event, other;

  factory IncomeCategory.fromString(String s) {
    switch (s) {
      case 'beer_sales': return IncomeCategory.beerSales;
      case 'merch_sales': return IncomeCategory.merchSales;
      case 'food_sales': return IncomeCategory.foodSales;
      case 'event': return IncomeCategory.event;
      default: return IncomeCategory.other;
    }
  }

  String get displayName {
    switch (this) {
      case IncomeCategory.beerSales: return 'Venta Cerveza';
      case IncomeCategory.merchSales: return 'Merchandising';
      case IncomeCategory.foodSales: return 'Alimentos';
      case IncomeCategory.event: return 'Eventos';
      case IncomeCategory.other: return 'Otro';
    }
  }
}

/// An income record.
class IncomeEntry extends Equatable {
  const IncomeEntry({
    required this.id,
    required this.incomeType,
    required this.category,
    required this.description,
    required this.amount,
    required this.paymentMethod,
    required this.profitCenter,
    required this.receivedDate,
    required this.createdAt,
    this.referenceId,
    this.receivedBy,
    this.notes,
  });

  final int id;
  final String incomeType;
  final String category;
  final String description;
  final double amount;
  final String paymentMethod;
  final String profitCenter;
  final DateTime receivedDate;
  final DateTime createdAt;
  final String? referenceId;
  final String? receivedBy;
  final String? notes;

  @override
  List<Object?> get props => [id, amount, category];
}

/// Aggregated income summary for a period.
class IncomeSummary extends Equatable {
  const IncomeSummary({
    required this.periodStart,
    required this.periodEnd,
    required this.totalIncome,
    required this.count,
    required this.byCategory,
    required this.byPaymentMethod,
    required this.byProfitCenter,
  });

  final DateTime periodStart;
  final DateTime periodEnd;
  final double totalIncome;
  final int count;
  final Map<String, double> byCategory;
  final Map<String, double> byPaymentMethod;
  final Map<String, double> byProfitCenter;

  @override
  List<Object?> get props => [totalIncome, count];
}
