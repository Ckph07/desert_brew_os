import 'package:equatable/equatable.dart';

class PayrollEntry extends Equatable {
  const PayrollEntry({
    required this.id,
    required this.employeeId,
    required this.periodStart,
    required this.periodEnd,
    required this.periodType,
    required this.daysWorked,
    required this.dailyRate,
    required this.baseSalary,
    required this.overtimeHours,
    required this.overtimeRate,
    required this.overtimeAmount,
    required this.tipsShare,
    required this.taxiShifts,
    required this.taxiTotal,
    required this.bonuses,
    required this.deductions,
    required this.totalPayment,
    required this.paymentStatus,
    required this.createdAt,
    this.tipPoolId,
    this.deductionNotes,
    this.paidAt,
    this.notes,
  });

  final int id;
  final int employeeId;
  final DateTime periodStart;
  final DateTime periodEnd;
  final String periodType;
  final int daysWorked;
  final double dailyRate;
  final double baseSalary;
  final double overtimeHours;
  final double overtimeRate;
  final double overtimeAmount;
  final double tipsShare;
  final int taxiShifts;
  final double taxiTotal;
  final double bonuses;
  final double deductions;
  final double totalPayment;
  final String paymentStatus;
  final DateTime createdAt;
  final int? tipPoolId;
  final String? deductionNotes;
  final DateTime? paidAt;
  final String? notes;

  bool get isPaid => paymentStatus.toUpperCase() == 'PAID';

  @override
  List<Object?> get props => [
    id,
    employeeId,
    periodStart,
    periodEnd,
    periodType,
    daysWorked,
    dailyRate,
    baseSalary,
    overtimeHours,
    overtimeRate,
    overtimeAmount,
    tipsShare,
    taxiShifts,
    taxiTotal,
    bonuses,
    deductions,
    totalPayment,
    paymentStatus,
    createdAt,
    tipPoolId,
    deductionNotes,
    paidAt,
    notes,
  ];
}
