import 'package:equatable/equatable.dart';

/// An expense record.
class ExpenseEntry extends Equatable {
  const ExpenseEntry({
    required this.id,
    required this.expenseType,
    required this.category,
    required this.description,
    required this.amount,
    required this.paymentMethod,
    required this.profitCenter,
    required this.paidDate,
    required this.createdAt,
    this.referenceId,
    this.supplierName,
    this.paidBy,
    this.notes,
  });

  final int id;
  final String expenseType;
  final String category;
  final String description;
  final double amount;
  final String paymentMethod;
  final String profitCenter;
  final DateTime paidDate;
  final DateTime createdAt;
  final String? referenceId;
  final String? supplierName;
  final String? paidBy;
  final String? notes;

  String get categoryDisplayName {
    const map = {
      'raw_materials': 'Materia Prima',
      'packaging': 'Empaque',
      'payroll': 'Nómina',
      'energy': 'Energía',
      'water': 'Agua',
      'gas': 'Gas',
      'rent': 'Renta',
      'maintenance': 'Mantenimiento',
      'transport': 'Transporte',
      'marketing': 'Marketing',
      'taxes': 'Impuestos',
      'other': 'Otro',
    };
    return map[category] ?? category;
  }

  @override
  List<Object?> get props => [id, amount, category];
}

/// Aggregated expense summary.
class ExpenseSummary extends Equatable {
  const ExpenseSummary({
    required this.periodStart,
    required this.periodEnd,
    required this.totalExpenses,
    required this.count,
    required this.byCategory,
    required this.byType,
    required this.byProfitCenter,
  });

  final DateTime periodStart;
  final DateTime periodEnd;
  final double totalExpenses;
  final int count;
  final Map<String, double> byCategory;
  final Map<String, double> byType;
  final Map<String, double> byProfitCenter;

  @override
  List<Object?> get props => [totalExpenses, count];
}
