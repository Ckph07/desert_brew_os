import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../core/sync/sync_manager.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/payroll_remote_datasource.dart';
import '../../data/repositories/payroll_repository_impl.dart';
import '../../domain/entities/payroll_employee.dart';
import '../../domain/entities/tip_pool.dart';
import '../../domain/repositories/payroll_repository.dart';

class TipPoolPage extends StatefulWidget {
  const TipPoolPage({super.key});

  @override
  State<TipPoolPage> createState() => _TipPoolPageState();
}

class _TipPoolPageState extends State<TipPoolPage> {
  late final PayrollRepository _repo;

  final _currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
  final _date = DateFormat('dd MMM yyyy');
  final _apiDate = DateFormat('yyyy-MM-dd');

  bool _loading = true;
  String? _errorMessage;

  List<TipPool> _tipPools = const [];
  List<PayrollEmployee> _eligibleEmployees = const [];

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
        _repo.getTipPools(limit: 40),
        _repo.getEmployees(department: 'TAPROOM', activeOnly: true),
      ]);

      final allTaproom = results[1] as List<PayrollEmployee>;

      if (!mounted) return;
      setState(() {
        _tipPools = results[0] as List<TipPool>;
        _eligibleEmployees =
            allTaproom.where((employee) => employee.eligibleForTips).toList();
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

  void _showSnack(String message, Color color) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message), backgroundColor: color));
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pool de Propinas'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadData,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openCreatePoolDialog,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo Pool'),
      ),
      body:
          _loading
              ? const Center(child: CircularProgressIndicator())
              : _errorMessage != null
              ? _ErrorView(message: _errorMessage!, onRetry: _loadData)
              : _buildBody(),
    );
  }

  Widget _buildBody() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
          child: ValueListenableBuilder<bool>(
            valueListenable: SyncManager.instance.isOnlineNotifier,
            builder: (context, online, _) {
              final color =
                  online ? DesertBrewColors.success : DesertBrewColors.warning;
              return Row(
                children: [
                  Icon(
                    online ? Icons.cloud_done_rounded : Icons.cloud_off_rounded,
                    size: 18,
                    color: color,
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
                    'Participantes elegibles: ${_eligibleEmployees.length}',
                    style: const TextStyle(color: DesertBrewColors.textHint),
                  ),
                ],
              );
            },
          ),
        ),
        Expanded(
          child:
              _tipPools.isEmpty
                  ? const _EmptyView(
                    icon: Icons.volunteer_activism_outlined,
                    message: 'Sin distribuciones de propinas registradas',
                  )
                  : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 6, 12, 20),
                    itemCount: _tipPools.length,
                    itemBuilder: (_, index) {
                      final pool = _tipPools[index];
                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      '${_date.format(pool.weekStart)} - ${_date.format(pool.weekEnd)}',
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
                                      color: DesertBrewColors.info.withValues(
                                        alpha: 0.15,
                                      ),
                                      borderRadius: BorderRadius.circular(999),
                                    ),
                                    child: Text(
                                      '${pool.numParticipants} participantes',
                                      style: const TextStyle(
                                        color: DesertBrewColors.info,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Total: ${_currency.format(pool.totalCollected)} · '
                                'Por persona: ${_currency.format(pool.perPersonShare)}',
                                style: const TextStyle(
                                  color: DesertBrewColors.textSecondary,
                                ),
                              ),
                              if (pool.participants.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Wrap(
                                  spacing: 6,
                                  runSpacing: 6,
                                  children:
                                      pool.participants
                                          .map(
                                            (p) => Chip(
                                              visualDensity:
                                                  VisualDensity.compact,
                                              label: Text(
                                                '${p.name}: ${_currency.format(p.share)}',
                                                style: const TextStyle(
                                                  fontSize: 11,
                                                ),
                                              ),
                                            ),
                                          )
                                          .toList(),
                                ),
                              ],
                              if (pool.notes != null &&
                                  pool.notes!.trim().isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Text(
                                  pool.notes!,
                                  style: const TextStyle(
                                    color: DesertBrewColors.textHint,
                                    fontSize: 12,
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

  Future<void> _openCreatePoolDialog() async {
    if (_eligibleEmployees.isEmpty) {
      _showSnack(
        'No hay empleados elegibles para propinas',
        DesertBrewColors.warning,
      );
      return;
    }

    final payload = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        var weekStart = DateTime.now().subtract(
          Duration(days: DateTime.now().weekday % 7),
        );
        var weekEnd = weekStart.add(const Duration(days: 6));
        final totalCtrl = TextEditingController();
        final notesCtrl = TextEditingController();
        final selectedIds = <int>{};

        Future<void> pickStart(
          void Function(void Function()) setStateDialog,
        ) async {
          final picked = await showDatePicker(
            context: context,
            initialDate: weekStart,
            firstDate: DateTime(2024),
            lastDate: DateTime(2035),
          );
          if (picked != null) {
            setStateDialog(() {
              weekStart = picked;
              weekEnd = picked.add(const Duration(days: 6));
            });
          }
        }

        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Nuevo tip pool semanal'),
              content: SizedBox(
                width: 520,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      OutlinedButton.icon(
                        onPressed: () => pickStart(setStateDialog),
                        icon: const Icon(Icons.event_rounded),
                        label: Text(
                          'Semana: ${_date.format(weekStart)} - ${_date.format(weekEnd)}',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: totalCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Total recolectado (MXN)',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: notesCtrl,
                        decoration: const InputDecoration(labelText: 'Notas'),
                        maxLines: 2,
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Participantes',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 6),
                      ..._eligibleEmployees.map(
                        (employee) => CheckboxListTile(
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          value: selectedIds.contains(employee.id),
                          onChanged: (checked) {
                            setStateDialog(() {
                              if (checked ?? false) {
                                selectedIds.add(employee.id);
                              } else {
                                selectedIds.remove(employee.id);
                              }
                            });
                          },
                          title: Text(employee.fullName),
                          subtitle: Text(employee.role),
                        ),
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
                    final total = double.tryParse(totalCtrl.text.trim());
                    if (total == null || total <= 0) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Total recolectado inválido'),
                          backgroundColor: DesertBrewColors.warning,
                        ),
                      );
                      return;
                    }
                    if (selectedIds.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Selecciona al menos 1 participante'),
                          backgroundColor: DesertBrewColors.warning,
                        ),
                      );
                      return;
                    }

                    Navigator.of(dialogContext).pop({
                      'week_start': _apiDate.format(weekStart),
                      'week_end': _apiDate.format(weekEnd),
                      'total_collected': total,
                      'participant_ids': selectedIds.toList(),
                      if (notesCtrl.text.trim().isNotEmpty)
                        'notes': notesCtrl.text.trim(),
                      'created_by': 'frontend',
                    });
                  },
                  child: const Text('Crear Pool'),
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
      path: '/api/v1/payroll/tip-pools',
      execute: () async {
        await _repo.createTipPool(payload);
      },
      successMessage: 'Tip pool creado',
      queuedMessage: 'Sin red: tip pool encolado',
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

class _EmptyView extends StatelessWidget {
  const _EmptyView({required this.icon, required this.message});

  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 52, color: DesertBrewColors.textHint),
          const SizedBox(height: 10),
          Text(
            message,
            style: const TextStyle(color: DesertBrewColors.textSecondary),
          ),
        ],
      ),
    );
  }
}
