import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';

/// Finance dashboard — Transfer pricing, income/expense, balance & cashflow.
///
/// Sprint 3.5 + 3.5b: 19 endpoints total.
class FinanceDashboardPage extends StatelessWidget {
  const FinanceDashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Finanzas')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Quick summary cards
            Row(
              children: [
                Expanded(
                  child: _SummaryCard(
                    icon: Icons.trending_up_rounded,
                    label: 'Ingresos',
                    value: '—',
                    color: DesertBrewColors.success,
                    onTap: () => context.go('/finance/income'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _SummaryCard(
                    icon: Icons.trending_down_rounded,
                    label: 'Egresos',
                    value: '—',
                    color: DesertBrewColors.error,
                    onTap: () => context.go('/finance/expenses'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Navigation list
            _NavTile(
              icon: Icons.account_balance_wallet_rounded,
              title: 'Balance y Flujo de Efectivo',
              subtitle: 'Income vs Expenses · Net Profit · Cashflow mensual',
              color: DesertBrewColors.primary,
              onTap: () => context.go('/finance/balance'),
            ),
            _NavTile(
              icon: Icons.swap_horiz_rounded,
              title: 'Transfer Pricing',
              subtitle: 'HOUSE +15% · GUEST 0% · COMMERCIAL 0% · MERCH +25%',
              color: DesertBrewColors.info,
              onTap: () => context.go('/finance/pricing-rules'),
            ),
            _NavTile(
              icon: Icons.compare_arrows_rounded,
              title: 'Transferencias Internas',
              subtitle: 'Factory → Taproom · Shadow Ledger',
              color: DesertBrewColors.warning,
              onTap: () => context.go('/finance/internal-transfers'),
            ),
            _NavTile(
              icon: Icons.pie_chart_rounded,
              title: 'P&L por Centro de Utilidad',
              subtitle: 'Fábrica vs Taproom vs Distribución',
              color: DesertBrewColors.accent,
              onTap: () => context.go('/finance/profit-center-summary'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 12),
              Text(
                value,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              Text(
                label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: DesertBrewColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NavTile extends StatelessWidget {
  const _NavTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.15),
          child: Icon(icon, color: color, size: 20),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          subtitle,
          style: TextStyle(color: DesertBrewColors.textHint, fontSize: 12),
        ),
        trailing: const Icon(
          Icons.chevron_right_rounded,
          color: DesertBrewColors.textHint,
        ),
        onTap: onTap,
      ),
    );
  }
}
