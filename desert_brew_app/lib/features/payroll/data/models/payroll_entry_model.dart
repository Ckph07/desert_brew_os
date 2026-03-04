import '../../domain/entities/payroll_entry.dart';

class PayrollEntryModel extends PayrollEntry {
  const PayrollEntryModel({
    required super.id,
    required super.employeeId,
    required super.periodStart,
    required super.periodEnd,
    required super.periodType,
    required super.daysWorked,
    required super.dailyRate,
    required super.baseSalary,
    required super.overtimeHours,
    required super.overtimeRate,
    required super.overtimeAmount,
    required super.tipsShare,
    required super.taxiShifts,
    required super.taxiTotal,
    required super.bonuses,
    required super.deductions,
    required super.totalPayment,
    required super.paymentStatus,
    required super.createdAt,
    super.tipPoolId,
    super.deductionNotes,
    super.paidAt,
    super.notes,
  });

  factory PayrollEntryModel.fromJson(Map<String, dynamic> json) {
    double parseNum(dynamic value) {
      if (value is num) return value.toDouble();
      return double.tryParse(value?.toString() ?? '0') ?? 0;
    }

    return PayrollEntryModel(
      id: json['id'] as int,
      employeeId: json['employee_id'] as int,
      periodStart: DateTime.parse(json['period_start'] as String),
      periodEnd: DateTime.parse(json['period_end'] as String),
      periodType: (json['period_type'] as String? ?? '').toUpperCase(),
      daysWorked: (json['days_worked'] as num?)?.toInt() ?? 0,
      dailyRate: parseNum(json['daily_rate']),
      baseSalary: parseNum(json['base_salary']),
      overtimeHours: parseNum(json['overtime_hours']),
      overtimeRate: parseNum(json['overtime_rate']),
      overtimeAmount: parseNum(json['overtime_amount']),
      tipsShare: parseNum(json['tips_share']),
      taxiShifts: (json['taxi_shifts'] as num?)?.toInt() ?? 0,
      taxiTotal: parseNum(json['taxi_total']),
      bonuses: parseNum(json['bonuses']),
      deductions: parseNum(json['deductions']),
      totalPayment: parseNum(json['total_payment']),
      paymentStatus: (json['payment_status'] as String? ?? '').toUpperCase(),
      createdAt: DateTime.parse(json['created_at'] as String),
      tipPoolId: json['tip_pool_id'] as int?,
      deductionNotes: json['deduction_notes'] as String?,
      paidAt:
          json['paid_at'] != null
              ? DateTime.parse(json['paid_at'] as String)
              : null,
      notes: json['notes'] as String?,
    );
  }
}
