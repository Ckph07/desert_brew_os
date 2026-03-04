import 'package:equatable/equatable.dart';

class PayrollEmployee extends Equatable {
  const PayrollEmployee({
    required this.id,
    required this.employeeCode,
    required this.fullName,
    required this.role,
    required this.department,
    required this.employmentType,
    required this.dailySalary,
    required this.eligibleForTips,
    required this.isActive,
    required this.hireDate,
    required this.createdAt,
    required this.updatedAt,
    this.monthlySalary,
    this.taxiAllowancePerShift,
    this.phone,
    this.email,
    this.emergencyContact,
    this.notes,
  });

  final int id;
  final String employeeCode;
  final String fullName;
  final String role;
  final String department;
  final String employmentType;
  final double dailySalary;
  final double? monthlySalary;
  final bool eligibleForTips;
  final double? taxiAllowancePerShift;
  final bool isActive;
  final DateTime hireDate;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? phone;
  final String? email;
  final String? emergencyContact;
  final String? notes;

  bool get isTemporary => employmentType.toUpperCase() == 'TEMPORARY';

  @override
  List<Object?> get props => [
    id,
    employeeCode,
    fullName,
    role,
    department,
    employmentType,
    dailySalary,
    monthlySalary,
    eligibleForTips,
    taxiAllowancePerShift,
    isActive,
    hireDate,
    createdAt,
    updatedAt,
    phone,
    email,
    emergencyContact,
    notes,
  ];
}
