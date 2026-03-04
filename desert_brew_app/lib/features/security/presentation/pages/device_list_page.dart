import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../core/sync/sync_manager.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/security_remote_datasource.dart';
import '../../data/repositories/security_repository_impl.dart';
import '../../domain/entities/security_device.dart';
import '../../domain/repositories/security_repository.dart';

/// Device enrollment admin page.
class DeviceListPage extends StatefulWidget {
  const DeviceListPage({super.key});

  @override
  State<DeviceListPage> createState() => _DeviceListPageState();
}

class _DeviceListPageState extends State<DeviceListPage> {
  late final SecurityRepository _repo;
  final _date = DateFormat('dd MMM yyyy · HH:mm');

  bool _loading = true;
  String? _errorMessage;

  String? _statusFilter;
  List<SecurityDevice> _devices = const [];
  SecurityEnrollmentStats _stats = const SecurityEnrollmentStats(
    byStatus: {},
    total: 0,
    staleDevices7d: 0,
  );

  @override
  void initState() {
    super.initState();
    _repo = SecurityRepositoryImpl(SecurityRemoteDataSource());
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });

    try {
      final results = await Future.wait([
        _repo.getDevices(status: _statusFilter, skip: 0, limit: 200),
        _repo.getEnrollmentStats(),
      ]);

      if (!mounted) return;
      setState(() {
        _devices = results[0] as List<SecurityDevice>;
        _stats = results[1] as SecurityEnrollmentStats;
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
        title: const Text('Seguridad — Enrollment'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadData,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openEnrollDialog,
        icon: const Icon(Icons.phonelink_setup_rounded),
        label: const Text('Enroll Device'),
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
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
          child: ValueListenableBuilder<bool>(
            valueListenable: SyncManager.instance.isOnlineNotifier,
            builder: (context, online, _) {
              return ValueListenableBuilder<int>(
                valueListenable: SyncManager.instance.pendingCountNotifier,
                builder: (context, pending, __) {
                  return Row(
                    children: [
                      Icon(
                        online
                            ? Icons.cloud_done_rounded
                            : Icons.cloud_off_rounded,
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
                        style: const TextStyle(
                          color: DesertBrewColors.textHint,
                        ),
                      ),
                    ],
                  );
                },
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(12),
          child: _StatsGrid(stats: _stats),
        ),
        SizedBox(
          height: 40,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            children: [
              _filterChip('Todos', null),
              const SizedBox(width: 8),
              _filterChip('Pending', 'pending'),
              const SizedBox(width: 8),
              _filterChip('Active', 'active'),
              const SizedBox(width: 8),
              _filterChip('Revoked', 'revoked'),
              const SizedBox(width: 8),
              _filterChip('Suspended', 'suspended'),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Expanded(
          child:
              _devices.isEmpty
                  ? const _EmptyView(
                    icon: Icons.security_outlined,
                    message: 'Sin dispositivos para el filtro seleccionado',
                  )
                  : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 20),
                    itemCount: _devices.length,
                    itemBuilder: (_, index) {
                      final device = _devices[index];
                      final color = _statusColor(device.status);

                      return Card(
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: color.withValues(alpha: 0.2),
                            child: Icon(
                              Icons.phone_android_rounded,
                              color: color,
                            ),
                          ),
                          title: Text(device.deviceId),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${device.deviceModel} · ${device.assignedUserName}',
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Enrolled: ${_date.format(device.enrolledAt)}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: DesertBrewColors.textHint,
                                ),
                              ),
                              Text(
                                device.lastHeartbeat != null
                                    ? 'Heartbeat: ${_date.format(device.lastHeartbeat!)} (${device.daysSinceHeartbeat}d)'
                                    : 'Heartbeat: sin registro',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: DesertBrewColors.textHint,
                                ),
                              ),
                            ],
                          ),
                          trailing: PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'approve') {
                                _approveDevice(device.deviceId);
                              } else if (value == 'revoke') {
                                _askRevokeReason(device.deviceId);
                              } else if (value == 'heartbeat') {
                                _sendHeartbeat(device.deviceId);
                              }
                            },
                            itemBuilder: (_) {
                              final items = <PopupMenuEntry<String>>[];
                              if (device.isPending) {
                                items.add(
                                  const PopupMenuItem(
                                    value: 'approve',
                                    child: Text('Approve'),
                                  ),
                                );
                              }
                              if (device.isActive) {
                                items.add(
                                  const PopupMenuItem(
                                    value: 'heartbeat',
                                    child: Text('Heartbeat'),
                                  ),
                                );
                              }
                              if (!device.isRevoked) {
                                items.add(
                                  const PopupMenuItem(
                                    value: 'revoke',
                                    child: Text('Revoke'),
                                  ),
                                );
                              }
                              return items;
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: color.withValues(alpha: 0.16),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(
                                device.status.toUpperCase(),
                                style: TextStyle(
                                  color: color,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
        ),
      ],
    );
  }

  Widget _filterChip(String label, String? value) {
    return FilterChip(
      selected: _statusFilter == value,
      onSelected: (_) {
        setState(() => _statusFilter = value);
        _loadData();
      },
      label: Text(label, style: const TextStyle(fontSize: 12)),
      selectedColor: DesertBrewColors.info.withValues(alpha: 0.18),
    );
  }

  Color _statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return DesertBrewColors.success;
      case 'pending':
        return DesertBrewColors.warning;
      case 'revoked':
        return DesertBrewColors.error;
      case 'suspended':
        return DesertBrewColors.info;
      default:
        return DesertBrewColors.textHint;
    }
  }

  Future<void> _approveDevice(String deviceId) async {
    await _runMutation(
      method: 'PATCH',
      path: '/api/v1/security/enrollments/$deviceId/approve',
      execute: () => _repo.approveDevice(deviceId: deviceId, adminUserId: 1),
      successMessage: 'Dispositivo aprobado',
      queuedMessage: 'Sin red: aprobación encolada',
    );
  }

  Future<void> _sendHeartbeat(String deviceId) async {
    await _runMutation(
      method: 'POST',
      path: '/api/v1/security/enrollments/$deviceId/heartbeat',
      execute: () => _repo.heartbeat(deviceId: deviceId),
      successMessage: 'Heartbeat enviado',
      queuedMessage: 'Sin red: heartbeat encolado',
    );
  }

  Future<void> _askRevokeReason(String deviceId) async {
    final reasonCtrl = TextEditingController();

    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Revocar dispositivo'),
          content: TextField(
            controller: reasonCtrl,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Razón de revocación'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () {
                final reason = reasonCtrl.text.trim();
                if (reason.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('La razón es obligatoria'),
                      backgroundColor: DesertBrewColors.warning,
                    ),
                  );
                  return;
                }
                Navigator.of(dialogContext).pop(reason);
              },
              child: const Text('Revocar'),
            ),
          ],
        );
      },
    );

    if (reason == null) return;

    await _runMutation(
      method: 'PATCH',
      path: '/api/v1/security/enrollments/$deviceId/revoke',
      execute:
          () => _repo.revokeDevice(
            deviceId: deviceId,
            reason: reason,
            adminUserId: 1,
          ),
      successMessage: 'Dispositivo revocado',
      queuedMessage: 'Sin red: revocación encolada',
    );
  }

  Future<void> _openEnrollDialog() async {
    final payload = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        final deviceIdCtrl = TextEditingController();
        final modelCtrl = TextEditingController();
        final osCtrl = TextEditingController();
        final keyCtrl = TextEditingController();
        final userIdCtrl = TextEditingController();
        final userNameCtrl = TextEditingController();

        return AlertDialog(
          title: const Text('Enroll device'),
          content: SizedBox(
            width: 520,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: deviceIdCtrl,
                    decoration: const InputDecoration(labelText: 'Device ID'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: modelCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Device model',
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: osCtrl,
                    decoration: const InputDecoration(labelText: 'OS version'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: keyCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Public key hex (64 chars)',
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: userIdCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'User ID'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: userNameCtrl,
                    decoration: const InputDecoration(labelText: 'User name'),
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
                final deviceId = deviceIdCtrl.text.trim();
                final model = modelCtrl.text.trim();
                final osVersion = osCtrl.text.trim();
                final publicKeyHex = keyCtrl.text.trim().toLowerCase();
                final userId = int.tryParse(userIdCtrl.text.trim());
                final userName = userNameCtrl.text.trim();

                final isHex = RegExp(r'^[0-9a-fA-F]+$').hasMatch(publicKeyHex);

                if (deviceId.isEmpty ||
                    model.isEmpty ||
                    osVersion.isEmpty ||
                    publicKeyHex.length != 64 ||
                    !isHex ||
                    userId == null ||
                    userName.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text(
                        'Completa todos los campos con formato válido',
                      ),
                      backgroundColor: DesertBrewColors.warning,
                    ),
                  );
                  return;
                }

                Navigator.of(dialogContext).pop({
                  'device_id': deviceId,
                  'device_model': model,
                  'os_version': osVersion,
                  'public_key_hex': publicKeyHex,
                  'user_id': userId,
                  'user_name': userName,
                });
              },
              child: const Text('Enviar enrollment'),
            ),
          ],
        );
      },
    );

    if (payload == null) return;

    await _runMutation(
      method: 'POST',
      path: '/api/v1/security/enroll',
      execute: () async {
        await _repo.enrollDevice(payload);
      },
      successMessage: 'Enrollment enviado',
      queuedMessage: 'Sin red: enrollment encolado',
    );
  }
}

class _StatsGrid extends StatelessWidget {
  const _StatsGrid({required this.stats});

  final SecurityEnrollmentStats stats;

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      childAspectRatio: 2.7,
      children: [
        _tile('Total', '${stats.total}', DesertBrewColors.primary),
        _tile('Activos', '${stats.active}', DesertBrewColors.success),
        _tile('Pendientes', '${stats.pending}', DesertBrewColors.warning),
        _tile('Stale >7d', '${stats.staleDevices7d}', DesertBrewColors.error),
      ],
    );
  }

  Widget _tile(String label, String value, Color color) {
    return Container(
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(color: DesertBrewColors.textSecondary),
          ),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
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
