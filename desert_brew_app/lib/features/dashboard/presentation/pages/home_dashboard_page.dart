import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';

/// Home dashboard — KPI overview across all services.
class HomeDashboardPage extends StatelessWidget {
  const HomeDashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Desert Brew OS'),
        actions: [
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Welcome header
            Text(
              '¡Buenos días, Cervecero! 🍺',
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Resumen del sistema',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: DesertBrewColors.textSecondary,
              ),
            ),
            const SizedBox(height: 24),

            // KPI cards grid
            _buildKpiGrid(context),

            const SizedBox(height: 24),

            // Quick actions
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
      ),
    );
  }

  Widget _buildKpiGrid(BuildContext context) {
    final kpis = [
      _KpiCardData(
        'Inventario',
        '—',
        Icons.inventory_2_rounded,
        DesertBrewColors.info,
        route: '/inventory',
      ),
      _KpiCardData(
        'Batches Activos',
        '—',
        Icons.science_rounded,
        DesertBrewColors.warning,
        route: '/production/batches',
      ),
      _KpiCardData(
        'Notas del Mes',
        '—',
        Icons.receipt_long_rounded,
        DesertBrewColors.success,
        route: '/sales/notes',
      ),
      _KpiCardData(
        'Kegs en Cliente',
        '—',
        Icons.local_shipping_rounded,
        DesertBrewColors.error,
        route: '/inventory/kegs',
      ),
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 1.4,
      ),
      itemCount: kpis.length,
      itemBuilder: (context, index) {
        final kpi = kpis[index];
        return Card(
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: kpi.route == null ? null : () => context.go(kpi.route!),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(kpi.icon, color: kpi.color, size: 28),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        kpi.value,
                        style: Theme.of(
                          context,
                        ).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: kpi.color,
                        ),
                      ),
                      Text(
                        kpi.label,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: DesertBrewColors.textSecondary,
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
        _actionChip(context, '📝 Nota de Venta', '/sales/notes'),
        _actionChip(context, '🔍 Escanear Keg', '/inventory/kegs'),
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
    this.route,
  });
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? route;
}
