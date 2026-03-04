import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../../core/sync/sync_manager.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/dashboard_remote_datasource.dart';
import '../../data/repositories/dashboard_repository_impl.dart';
import '../../domain/entities/global_kpi_snapshot.dart';
import '../../domain/repositories/dashboard_repository.dart';

/// Home dashboard — KPI overview across all services.
class HomeDashboardPage extends StatefulWidget {
  const HomeDashboardPage({super.key});

  @override
  State<HomeDashboardPage> createState() => _HomeDashboardPageState();
}

class _HomeDashboardPageState extends State<HomeDashboardPage> {
  late final DashboardRepository _repo;
  final _currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
  final _time = DateFormat('dd MMM HH:mm');

  bool _loading = true;
  String? _errorMessage;
  GlobalKpiSnapshot? _snapshot;

  @override
  void initState() {
    super.initState();
    _repo = DashboardRepositoryImpl(DashboardRemoteDataSource());
    _loadKpis();
  }

  Future<void> _loadKpis() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });

    try {
      final snapshot = await _repo.getGlobalKpis(allowStaleFallback: true);
      if (!mounted) return;
      setState(() {
        _snapshot = snapshot;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _errorMessage = error.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Desert Brew OS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadKpis,
          ),
          IconButton(
            icon: const Icon(Icons.settings_rounded),
            onPressed:
                () => ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'Configuración estará disponible en el siguiente corte',
                    ),
                    backgroundColor: DesertBrewColors.info,
                  ),
                ),
          ),
        ],
      ),
      body:
          _loading
              ? const Center(child: CircularProgressIndicator())
              : _errorMessage != null
              ? _ErrorView(message: _errorMessage!, onRetry: _loadKpis)
              : _buildBody(context),
    );
  }

  Widget _buildBody(BuildContext context) {
    final snapshot = _snapshot;
    if (snapshot == null) {
      return _ErrorView(
        message: 'No se pudo construir el dashboard.',
        onRetry: _loadKpis,
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '¡Buenos días, Cervecero! 🍺',
            style: Theme.of(
              context,
            ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Última actualización: ${_time.format(snapshot.fetchedAt)}'
            '${snapshot.isStale ? ' (cache offline)' : ''}',
            style: const TextStyle(color: DesertBrewColors.textSecondary),
          ),
          const SizedBox(height: 12),
          _buildSyncBar(),
          if (snapshot.isStale) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: DesertBrewColors.warning.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                'Mostrando snapshot en caché por falta de conectividad.',
                style: TextStyle(color: DesertBrewColors.warning),
              ),
            ),
          ],
          const SizedBox(height: 18),
          _buildKpiGrid(context, snapshot),
          const SizedBox(height: 24),
          Text(
            'Acciones Rápidas',
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildQuickActions(context),
        ],
      ),
    );
  }

  Widget _buildSyncBar() {
    return ValueListenableBuilder<bool>(
      valueListenable: SyncManager.instance.isOnlineNotifier,
      builder: (context, online, _) {
        return ValueListenableBuilder<int>(
          valueListenable: SyncManager.instance.pendingCountNotifier,
          builder: (context, pending, _) {
            final color =
                online ? DesertBrewColors.success : DesertBrewColors.warning;
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: DesertBrewColors.surface,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
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
                    'Outbox: $pending',
                    style: const TextStyle(color: DesertBrewColors.textHint),
                  ),
                  if (online && pending > 0) ...[
                    const SizedBox(width: 10),
                    TextButton(
                      onPressed: () async {
                        await SyncManager.instance.flushNow();
                        if (!mounted) return;
                        _loadKpis();
                      },
                      child: const Text('Sincronizar'),
                    ),
                  ],
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildKpiGrid(BuildContext context, GlobalKpiSnapshot snapshot) {
    final kpis = [
      _KpiCardData(
        'Inventario MXN',
        _currency.format(snapshot.inventoryValueMxn),
        Icons.inventory_2_rounded,
        DesertBrewColors.info,
        route: '/inventory',
      ),
      _KpiCardData(
        'Batches Activos',
        '${snapshot.activeBatches}',
        Icons.science_rounded,
        DesertBrewColors.warning,
        route: '/production/batches',
      ),
      _KpiCardData(
        'Notas del Mes',
        '${snapshot.monthlySalesNotes}',
        Icons.receipt_long_rounded,
        DesertBrewColors.success,
        route: '/sales/notes',
      ),
      _KpiCardData(
        'Kegs en Cliente',
        '${snapshot.kegsInClient}',
        Icons.local_shipping_rounded,
        DesertBrewColors.error,
        route: '/inventory/kegs',
      ),
      _KpiCardData(
        'Pagos Pendientes',
        '${snapshot.pendingPayrollEntries}',
        Icons.payments_rounded,
        DesertBrewColors.info,
        route: '/payroll',
      ),
      _KpiCardData(
        'Devices Activos',
        '${snapshot.activeDevices}',
        Icons.security_rounded,
        DesertBrewColors.primary,
        route: '/security',
      ),
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 1.35,
      ),
      itemCount: kpis.length,
      itemBuilder: (context, index) {
        final kpi = kpis[index];
        return Card(
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => context.go(kpi.route),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(kpi.icon, color: kpi.color, size: 26),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        kpi.value,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: kpi.color,
                        ),
                      ),
                      Text(
                        kpi.label,
                        style: const TextStyle(
                          color: DesertBrewColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        _actionChip(context, '📦 Recibir Stock', '/inventory/receive'),
        _actionChip(context, '🍺 Nueva Receta', '/production'),
        _actionChip(context, '📝 Nota de Venta', '/sales/notes/create'),
        _actionChip(context, '👥 Nómina', '/payroll'),
        _actionChip(context, '🔐 Security', '/security'),
      ],
    );
  }

  Widget _actionChip(BuildContext context, String label, String route) {
    return ActionChip(label: Text(label), onPressed: () => context.go(route));
  }
}

class _KpiCardData {
  const _KpiCardData(
    this.label,
    this.value,
    this.icon,
    this.color, {
    required this.route,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String route;
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
