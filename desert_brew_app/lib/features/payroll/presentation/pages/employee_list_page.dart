import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../../core/sync/sync_manager.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/payroll_remote_datasource.dart';
import '../../data/repositories/payroll_repository_impl.dart';
import '../../domain/entities/payroll_employee.dart';
import '../../domain/entities/payroll_entry.dart';
import '../../domain/repositories/payroll_repository.dart';

/// Payroll home: employees + payroll entries.
class EmployeeListPage extends StatefulWidget {
  const EmployeeListPage({super.key});

  @override
  State<EmployeeListPage> createState() => _EmployeeListPageState();
}

class _EmployeeListPageState extends State<EmployeeListPage> {
  late final PayrollRepository _repo;
  final _currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
  final _date = DateFormat('dd MMM yyyy');

  bool _loading = true;
  String? _errorMessage;

  String? _employeeDepartment;
  String? _employeeType;
  String? _entryStatus;

  List<PayrollEmployee> _employees = const [];
  List<PayrollEntry> _entries = const [];

  @override
  void initState() {
    super.initState();
    _repo = PayrollRepositoryImpl(PayrollRemoteDataSource());
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });

    try {
      final results = await Future.wait([
        _repo.getEmployees(
          department: _employeeDepartment,
          employmentType: _employeeType,
          activeOnly: true,
        ),
        _repo.getPayrollEntries(paymentStatus: _entryStatus, limit: 120),
      ]);

      if (!mounted) return;
      setState(() {
        _employees = results[0] as List<PayrollEmployee>;
        _entries = results[1] as List<PayrollEntry>;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _errorMessage = _readableError(error);
      });
    }
  }

  String _readableError(Object error) {
    if (error is DioException) {
      final detail = error.response?.data;
      if (detail is Map<String, dynamic> && detail['detail'] != null) {
        return detail['detail'].toString();
      }
      return error.message ?? 'No se pudo completar la operación.';
    }
    return error.toString();
  }

  Future<void> _runMutation({
    required String method,
    required String path,
    required Future<void> Function() execute,
    required String successMessage,
    required String queuedMessage,
  }) async {
    final sync = SyncManager.instance;
    final online = await sync.refreshConnectivity();

    if (!online) {
      sync.enqueueOperation(method: method, path: path, execute: execute);
      if (mounted) {
        _showSnack(queuedMessage, DesertBrewColors.warning);
      }
      return;
    }

    try {
      await execute();
      await _loadData();
      if (!mounted) return;
      _showSnack(successMessage, DesertBrewColors.success);
    } on DioException catch (error) {
      if (sync.shouldQueueOnError(error)) {
        sync.enqueueOperation(method: method, path: path, execute: execute);
        if (mounted) {
          _showSnack(queuedMessage, DesertBrewColors.warning);
        }
        return;
      }
      if (mounted) {
        _showSnack(_readableError(error), DesertBrewColors.error);
      }
    } catch (error) {
      if (mounted) {
        _showSnack(_readableError(error), DesertBrewColors.error);
      }
    }
  }

  void _showSnack(String message, Color color) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message), backgroundColor: color));
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Nómina'),
          actions: [
            IconButton(
              tooltip: 'Tip Pool',
              onPressed: () => context.go('/payroll/tip-pool'),
              icon: const Icon(Icons.volunteer_activism_rounded),
            ),
            PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'employee') {
                  _openCreateEmployeeDialog();
                } else {
                  _openCreateEntryDialog();
                }
              },
              itemBuilder:
                  (_) => const [
                    PopupMenuItem(
                      value: 'employee',
                      child: Text('Nuevo Empleado'),
                    ),
                    PopupMenuItem(
                      value: 'entry',
                      child: Text('Nueva Entrada Nómina'),
                    ),
                  ],
            ),
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              onPressed: _loadData,
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.badge_rounded), text: 'Empleados'),
              Tab(icon: Icon(Icons.payments_rounded), text: 'Entradas'),
            ],
          ),
        ),
        body: Column(
          children: [
            _buildSyncBanner(),
            Expanded(
              child:
                  _loading
                      ? const Center(child: CircularProgressIndicator())
                      : _errorMessage != null
                      ? _ErrorView(message: _errorMessage!, onRetry: _loadData)
                      : TabBarView(
                        children: [_buildEmployeesTab(), _buildEntriesTab()],
                      ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSyncBanner() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 6),
      child: ValueListenableBuilder<bool>(
        valueListenable: SyncManager.instance.isOnlineNotifier,
        builder: (context, online, _) {
          return ValueListenableBuilder<int>(
            valueListenable: SyncManager.instance.pendingCountNotifier,
            builder: (context, pending, _) {
              return Row(
                children: [
                  Icon(
                    online ? Icons.cloud_done_rounded : Icons.cloud_off_rounded,
                    size: 18,
                    color:
                        online
                            ? DesertBrewColors.success
                            : DesertBrewColors.warning,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    online ? 'Online' : 'Offline',
                    style: const TextStyle(
                      color: DesertBrewColors.textSecondary,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Outbox: $pending',
                    style: const TextStyle(color: DesertBrewColors.textHint),
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildEmployeesTab() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String?>(
                  value: _employeeDepartment,
                  decoration: const InputDecoration(labelText: 'Departamento'),
                  items: const [
                    DropdownMenuItem<String?>(
                      value: null,
                      child: Text('Todos'),
                    ),
                    DropdownMenuItem(
                      value: 'PRODUCTION',
                      child: Text('Producción'),
                    ),
                    DropdownMenuItem(value: 'TAPROOM', child: Text('Taproom')),
                    DropdownMenuItem(
                      value: 'LOGISTICS',
                      child: Text('Logística'),
                    ),
                    DropdownMenuItem(value: 'ADMIN', child: Text('Admin')),
                  ],
                  onChanged: (value) {
                    setState(() => _employeeDepartment = value);
                    _loadData();
                  },
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: DropdownButtonFormField<String?>(
                  value: _employeeType,
                  decoration: const InputDecoration(labelText: 'Tipo'),
                  items: const [
                    DropdownMenuItem<String?>(
                      value: null,
                      child: Text('Todos'),
                    ),
                    DropdownMenuItem(value: 'FIXED', child: Text('Fijo')),
                    DropdownMenuItem(
                      value: 'TEMPORARY',
                      child: Text('Temporal'),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() => _employeeType = value);
                    _loadData();
                  },
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child:
              _employees.isEmpty
                  ? const _EmptyState(
                    icon: Icons.people_outline_rounded,
                    title: 'Sin empleados para el filtro seleccionado',
                  )
                  : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
                    itemCount: _employees.length,
                    itemBuilder: (_, index) {
                      final employee = _employees[index];
                      return Card(
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 4,
                          ),
                          leading: CircleAvatar(
                            backgroundColor:
                                employee.eligibleForTips
                                    ? DesertBrewColors.info.withValues(
                                      alpha: 0.2,
                                    )
                                    : DesertBrewColors.surface,
                            child: Icon(
                              employee.eligibleForTips
                                  ? Icons.local_bar_rounded
                                  : Icons.badge_rounded,
                              color: DesertBrewColors.primary,
                            ),
                          ),
                          title: Text(employee.fullName),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${employee.employeeCode} · ${employee.role}',
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${employee.department} · ${employee.employmentType}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: DesertBrewColors.textHint,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Diario ${_currency.format(employee.dailySalary)}'
                                '${employee.monthlySalary != null ? ' · Mensual ${_currency.format(employee.monthlySalary)}' : ''}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: DesertBrewColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
        ),
      ],
    );
  }

  Widget _buildEntriesTab() {
    final employeesById = {
      for (final employee in _employees) employee.id: employee,
    };

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: DropdownButtonFormField<String?>(
            value: _entryStatus,
            decoration: const InputDecoration(labelText: 'Estatus pago'),
            items: const [
              DropdownMenuItem<String?>(value: null, child: Text('Todos')),
              DropdownMenuItem(value: 'PENDING', child: Text('Pendiente')),
              DropdownMenuItem(value: 'PAID', child: Text('Pagado')),
            ],
            onChanged: (value) {
              setState(() => _entryStatus = value);
              _loadData();
            },
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child:
              _entries.isEmpty
                  ? const _EmptyState(
                    icon: Icons.payments_outlined,
                    title: 'Sin entradas de nómina para el filtro seleccionado',
                  )
                  : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
                    itemCount: _entries.length,
                    itemBuilder: (_, index) {
                      final entry = _entries[index];
                      final employee = employeesById[entry.employeeId];

                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      employee?.fullName ??
                                          'Empleado #${entry.employeeId}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 10,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color:
                                          entry.isPaid
                                              ? DesertBrewColors.success
                                                  .withValues(alpha: 0.16)
                                              : DesertBrewColors.warning
                                                  .withValues(alpha: 0.16),
                                      borderRadius: BorderRadius.circular(999),
                                    ),
                                    child: Text(
                                      entry.paymentStatus,
                                      style: TextStyle(
                                        color:
                                            entry.isPaid
                                                ? DesertBrewColors.success
                                                : DesertBrewColors.warning,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '${_date.format(entry.periodStart)} - ${_date.format(entry.periodEnd)} · ${entry.periodType}',
                                style: const TextStyle(
                                  color: DesertBrewColors.textSecondary,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Total ${_currency.format(entry.totalPayment)} · Base ${_currency.format(entry.baseSalary)}',
                                style: const TextStyle(
                                  color: DesertBrewColors.textHint,
                                ),
                              ),
                              if (!entry.isPaid) ...[
                                const SizedBox(height: 8),
                                Align(
                                  alignment: Alignment.centerRight,
                                  child: OutlinedButton.icon(
                                    onPressed: () => _markEntryAsPaid(entry.id),
                                    icon: const Icon(
                                      Icons.check_circle_outline_rounded,
                                    ),
                                    label: const Text('Marcar Pagado'),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      );
                    },
                  ),
        ),
      ],
    );
  }

  Future<void> _markEntryAsPaid(int entryId) async {
    await _runMutation(
      method: 'PATCH',
      path: '/api/v1/payroll/entries/$entryId/pay',
      execute: () async {
        await _repo.markEntryAsPaid(entryId);
      },
      successMessage: 'Entrada marcada como pagada',
      queuedMessage: 'Sin red: pago encolado para sincronización',
    );
  }

  Future<void> _openCreateEmployeeDialog() async {
    final payload = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        final nameCtrl = TextEditingController();
        final roleCtrl = TextEditingController();
        final salaryCtrl = TextEditingController();
        final taxiCtrl = TextEditingController(text: '0');

        var department = 'PRODUCTION';
        var employmentType = 'FIXED';
        var eligibleForTips = false;

        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Nuevo empleado'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: nameCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Nombre completo',
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: roleCtrl,
                      decoration: const InputDecoration(labelText: 'Rol'),
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: department,
                      decoration: const InputDecoration(
                        labelText: 'Departamento',
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'PRODUCTION',
                          child: Text('Producción'),
                        ),
                        DropdownMenuItem(
                          value: 'TAPROOM',
                          child: Text('Taproom'),
                        ),
                        DropdownMenuItem(
                          value: 'LOGISTICS',
                          child: Text('Logística'),
                        ),
                        DropdownMenuItem(value: 'ADMIN', child: Text('Admin')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setStateDialog(() {
                          department = value;
                          if (department != 'TAPROOM') {
                            eligibleForTips = false;
                          }
                        });
                      },
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: employmentType,
                      decoration: const InputDecoration(
                        labelText: 'Tipo empleo',
                      ),
                      items: const [
                        DropdownMenuItem(value: 'FIXED', child: Text('Fijo')),
                        DropdownMenuItem(
                          value: 'TEMPORARY',
                          child: Text('Temporal'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setStateDialog(() => employmentType = value);
                      },
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: salaryCtrl,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Salario diario (MXN)',
                      ),
                    ),
                    const SizedBox(height: 8),
                    if (department == 'TAPROOM')
                      CheckboxListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        value: eligibleForTips,
                        onChanged:
                            (value) => setStateDialog(
                              () => eligibleForTips = value ?? false,
                            ),
                        title: const Text('Elegible para propinas'),
                      ),
                    TextField(
                      controller: taxiCtrl,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Apoyo taxi por turno',
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancelar'),
                ),
                FilledButton(
                  onPressed: () {
                    final name = nameCtrl.text.trim();
                    final role = roleCtrl.text.trim();
                    final dailySalary = double.tryParse(salaryCtrl.text.trim());
                    final taxi = double.tryParse(taxiCtrl.text.trim()) ?? 0;

                    if (name.isEmpty ||
                        role.isEmpty ||
                        dailySalary == null ||
                        dailySalary <= 0) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text(
                            'Completa nombre, rol y salario diario válido',
                          ),
                          backgroundColor: DesertBrewColors.warning,
                        ),
                      );
                      return;
                    }

                    Navigator.of(dialogContext).pop({
                      'full_name': name,
                      'role': role.toUpperCase(),
                      'department': department,
                      'employment_type': employmentType,
                      'daily_salary': dailySalary,
                      'eligible_for_tips': eligibleForTips,
                      'taxi_allowance_per_shift': taxi,
                    });
                  },
                  child: const Text('Guardar'),
                ),
              ],
            );
          },
        );
      },
    );

    if (payload == null) return;

    await _runMutation(
      method: 'POST',
      path: '/api/v1/payroll/employees',
      execute: () async {
        await _repo.createEmployee(payload);
      },
      successMessage: 'Empleado creado',
      queuedMessage: 'Sin red: alta de empleado encolada',
    );
  }

  Future<void> _openCreateEntryDialog() async {
    if (_employees.isEmpty) {
      _showSnack(
        'No hay empleados activos para crear nómina',
        DesertBrewColors.warning,
      );
      return;
    }

    final payload = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        var selectedEmployeeId = _employees.first.id;
        var periodType = 'WEEKLY';
        var periodStart = DateTime.now().subtract(const Duration(days: 6));
        var periodEnd = DateTime.now();

        final daysWorkedCtrl = TextEditingController(text: '6');
        final overtimeHoursCtrl = TextEditingController(text: '0');
        final overtimeRateCtrl = TextEditingController(text: '0');
        final tipsCtrl = TextEditingController(text: '0');
        final taxiShiftCtrl = TextEditingController(text: '0');
        final bonusesCtrl = TextEditingController(text: '0');
        final deductionsCtrl = TextEditingController(text: '0');
        final notesCtrl = TextEditingController();

        Future<void> pickStart(
          void Function(void Function()) setStateDialog,
        ) async {
          final picked = await showDatePicker(
            context: context,
            initialDate: periodStart,
            firstDate: DateTime(2024),
            lastDate: DateTime(2035),
          );
          if (picked != null) {
            setStateDialog(() => periodStart = picked);
          }
        }

        Future<void> pickEnd(
          void Function(void Function()) setStateDialog,
        ) async {
          final picked = await showDatePicker(
            context: context,
            initialDate: periodEnd,
            firstDate: DateTime(2024),
            lastDate: DateTime(2035),
          );
          if (picked != null) {
            setStateDialog(() => periodEnd = picked);
          }
        }

        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Nueva entrada de nómina'),
              content: SizedBox(
                width: 460,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      DropdownButtonFormField<int>(
                        value: selectedEmployeeId,
                        decoration: const InputDecoration(
                          labelText: 'Empleado',
                        ),
                        items:
                            _employees
                                .map(
                                  (employee) => DropdownMenuItem(
                                    value: employee.id,
                                    child: Text(employee.fullName),
                                  ),
                                )
                                .toList(),
                        onChanged: (value) {
                          if (value == null) return;
                          setStateDialog(() => selectedEmployeeId = value);
                        },
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        value: periodType,
                        decoration: const InputDecoration(labelText: 'Periodo'),
                        items: const [
                          DropdownMenuItem(
                            value: 'DAILY',
                            child: Text('Diario'),
                          ),
                          DropdownMenuItem(
                            value: 'WEEKLY',
                            child: Text('Semanal'),
                          ),
                          DropdownMenuItem(
                            value: 'BIWEEKLY',
                            child: Text('Quincenal'),
                          ),
                          DropdownMenuItem(
                            value: 'MONTHLY',
                            child: Text('Mensual'),
                          ),
                        ],
                        onChanged: (value) {
                          if (value == null) return;
                          setStateDialog(() => periodType = value);
                        },
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () => pickStart(setStateDialog),
                              icon: const Icon(Icons.event_rounded),
                              label: Text(
                                'Inicio: ${_date.format(periodStart)}',
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () => pickEnd(setStateDialog),
                              icon: const Icon(Icons.event_available_rounded),
                              label: Text('Fin: ${_date.format(periodEnd)}'),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: daysWorkedCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Días trabajados',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: overtimeHoursCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Horas extra',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: overtimeRateCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Tarifa hora extra',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: tipsCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Propinas',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: taxiShiftCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Turnos con taxi',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: bonusesCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(labelText: 'Bonos'),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: deductionsCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Deducciones',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: notesCtrl,
                        decoration: const InputDecoration(labelText: 'Notas'),
                        maxLines: 2,
                      ),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancelar'),
                ),
                FilledButton(
                  onPressed: () {
                    final daysWorked = int.tryParse(daysWorkedCtrl.text.trim());
                    if (daysWorked == null || daysWorked < 0) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Días trabajados inválido'),
                          backgroundColor: DesertBrewColors.warning,
                        ),
                      );
                      return;
                    }

                    final overtimeHours =
                        double.tryParse(overtimeHoursCtrl.text.trim()) ?? 0;
                    final overtimeRate =
                        double.tryParse(overtimeRateCtrl.text.trim()) ?? 0;
                    final tipsShare =
                        double.tryParse(tipsCtrl.text.trim()) ?? 0;
                    final taxiShifts =
                        int.tryParse(taxiShiftCtrl.text.trim()) ?? 0;
                    final bonuses =
                        double.tryParse(bonusesCtrl.text.trim()) ?? 0;
                    final deductions =
                        double.tryParse(deductionsCtrl.text.trim()) ?? 0;

                    Navigator.of(dialogContext).pop({
                      'employee_id': selectedEmployeeId,
                      'period_start': periodStart.toIso8601String(),
                      'period_end': periodEnd.toIso8601String(),
                      'period_type': periodType,
                      'days_worked': daysWorked,
                      'overtime_hours': overtimeHours,
                      'overtime_rate': overtimeRate,
                      'tips_share': tipsShare,
                      'taxi_shifts': taxiShifts,
                      'bonuses': bonuses,
                      'deductions': deductions,
                      if (notesCtrl.text.trim().isNotEmpty)
                        'notes': notesCtrl.text.trim(),
                    });
                  },
                  child: const Text('Crear'),
                ),
              ],
            );
          },
        );
      },
    );

    if (payload == null) return;

    await _runMutation(
      method: 'POST',
      path: '/api/v1/payroll/entries',
      execute: () async {
        await _repo.createPayrollEntry(payload);
      },
      successMessage: 'Entrada de nómina creada',
      queuedMessage: 'Sin red: entrada de nómina encolada',
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.error_outline_rounded,
              color: DesertBrewColors.error,
              size: 42,
            ),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 10),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title});

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 52, color: DesertBrewColors.textHint),
          const SizedBox(height: 10),
          Text(
            title,
            style: const TextStyle(color: DesertBrewColors.textSecondary),
          ),
        ],
      ),
    );
  }
}
