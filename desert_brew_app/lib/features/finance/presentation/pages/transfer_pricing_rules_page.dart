import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/finance_remote_datasource.dart';
import '../../data/repositories/finance_repository_impl.dart';

class TransferPricingRulesPage extends StatelessWidget {
  const TransferPricingRulesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final repo = FinanceRepositoryImpl(FinanceRemoteDataSource());
    return Scaffold(
      appBar: AppBar(title: const Text('Transfer Pricing Rules')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: repo.getPricingRules(),
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData) {
            return Center(
              child: Text(
                snapshot.error?.toString() ?? 'No se pudieron cargar reglas',
                style: const TextStyle(color: DesertBrewColors.error),
              ),
            );
          }
          final rules = snapshot.data!;
          if (rules.isEmpty) {
            return const Center(
              child: Text(
                'Sin reglas activas',
                style: TextStyle(color: DesertBrewColors.textHint),
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: rules.length,
            itemBuilder: (_, i) {
              final rule = rules[i];
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  title: Text(rule['rule_name']?.toString() ?? 'Rule'),
                  subtitle: Text(
                    '${rule['origin_type']} · ${rule['strategy']}',
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 12,
                    ),
                  ),
                  trailing: Text(
                    '${(rule['markup_percentage'] as num?)?.toStringAsFixed(2) ?? '0.00'}%',
                    style: const TextStyle(
                      color: DesertBrewColors.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
