import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/finance_remote_datasource.dart';
import '../../data/repositories/finance_repository_impl.dart';

class ProfitCenterSummaryPage extends StatefulWidget {
  const ProfitCenterSummaryPage({super.key});

  @override
  State<ProfitCenterSummaryPage> createState() =>
      _ProfitCenterSummaryPageState();
}

class _ProfitCenterSummaryPageState extends State<ProfitCenterSummaryPage> {
  String _profitCenter = 'factory';

  @override
  Widget build(BuildContext context) {
    final repo = FinanceRepositoryImpl(FinanceRemoteDataSource());
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    return Scaffold(
      appBar: AppBar(title: const Text('P&L por Centro de Utilidad')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: DropdownButtonFormField<String>(
              value: _profitCenter,
              decoration: const InputDecoration(labelText: 'Centro'),
              items: const [
                DropdownMenuItem(value: 'factory', child: Text('Factory')),
                DropdownMenuItem(value: 'taproom', child: Text('Taproom')),
              ],
              onChanged: (v) => setState(() => _profitCenter = v ?? 'factory'),
            ),
          ),
          Expanded(
            child: FutureBuilder<Map<String, dynamic>>(
              future: repo.getProfitCenterSummary(_profitCenter),
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData) {
                  return Center(
                    child: Text(
                      snapshot.error?.toString() ??
                          'No se pudo cargar el resumen',
                      style: const TextStyle(color: DesertBrewColors.error),
                    ),
                  );
                }
                final data = snapshot.data!;
                return ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _MetricTile(
                      'Revenue',
                      currency.format(
                        (data['total_revenue'] as num?)?.toDouble() ?? 0,
                      ),
                      DesertBrewColors.success,
                    ),
                    _MetricTile(
                      'COGS',
                      currency.format(
                        (data['total_cogs'] as num?)?.toDouble() ?? 0,
                      ),
                      DesertBrewColors.warning,
                    ),
                    _MetricTile(
                      'Profit',
                      currency.format(
                        (data['total_profit'] as num?)?.toDouble() ?? 0,
                      ),
                      DesertBrewColors.primary,
                    ),
                    _MetricTile(
                      'Margin',
                      '${(data['profit_margin_percentage'] as num?)?.toStringAsFixed(2) ?? '0.00'}%',
                      DesertBrewColors.accent,
                    ),
                    _MetricTile(
                      'Transferencias',
                      '${(data['transfer_count'] as num?)?.toInt() ?? 0}',
                      DesertBrewColors.textSecondary,
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile(this.label, this.value, this.color);
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(label),
        trailing: Text(
          value,
          style: TextStyle(color: color, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}
