import '../../domain/entities/payroll_employee.dart';

class PayrollEmployeeModel extends PayrollEmployee {
  const PayrollEmployeeModel({
    required super.id,
    required super.employeeCode,
    required super.fullName,
    required super.role,
    required super.department,
    required super.employmentType,
    required super.dailySalary,
    required super.eligibleForTips,
    required super.isActive,
    required super.hireDate,
    required super.createdAt,
    required super.updatedAt,
    super.monthlySalary,
    super.taxiAllowancePerShift,
    super.phone,
    super.email,
    super.emergencyContact,
    super.notes,
  });

  factory PayrollEmployeeModel.fromJson(Map<String, dynamic> json) {
    double? parseNum(dynamic value) {
      if (value == null) return null;
      if (value is num) return value.toDouble();
      return double.tryParse(value.toString());
    }

    return PayrollEmployeeModel(
      id: json['id'] as int,
      employeeCode: json['employee_code'] as String,
      fullName: json['full_name'] as String,
      role: (json['role'] as String? ?? '').toUpperCase(),
      department: (json['department'] as String? ?? '').toUpperCase(),
      employmentType: (json['employment_type'] as String? ?? '').toUpperCase(),
      dailySalary: parseNum(json['daily_salary']) ?? 0,
      monthlySalary: parseNum(json['monthly_salary']),
      eligibleForTips: json['eligible_for_tips'] as bool? ?? false,
      taxiAllowancePerShift: parseNum(json['taxi_allowance_per_shift']),
      isActive: json['is_active'] as bool? ?? true,
      hireDate: DateTime.parse(json['hire_date'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      phone: json['phone'] as String?,
      email: json['email'] as String?,
      emergencyContact: json['emergency_contact'] as String?,
      notes: json['notes'] as String?,
    );
  }
}
