import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/finance_remote_datasource.dart';
import '../../data/repositories/finance_repository_impl.dart';

class InternalTransfersPage extends StatelessWidget {
  const InternalTransfersPage({super.key});

  @override
  Widget build(BuildContext context) {
    final repo = FinanceRepositoryImpl(FinanceRemoteDataSource());
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final dateFmt = DateFormat('dd/MM/yy HH:mm');
    return Scaffold(
      appBar: AppBar(title: const Text('Transferencias Internas')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: repo.getInternalTransfers(limit: 200),
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData) {
            return Center(
              child: Text(
                snapshot.error?.toString() ??
                    'No se pudieron cargar transferencias',
                style: const TextStyle(color: DesertBrewColors.error),
              ),
            );
          }
          final transfers = snapshot.data!;
          if (transfers.isEmpty) {
            return const Center(
              child: Text(
                'Sin transferencias registradas',
                style: TextStyle(color: DesertBrewColors.textHint),
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: transfers.length,
            itemBuilder: (_, i) {
              final t = transfers[i];
              final dateRaw = t['transfer_date']?.toString();
              final transferDate =
                  dateRaw != null
                      ? DateTime.tryParse(dateRaw)?.toLocal()
                      : null;
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  title: Text(
                    '${t['product_name'] ?? t['product_sku']}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    '${t['from_profit_center']} -> ${t['to_profit_center']} · ${transferDate != null ? dateFmt.format(transferDate) : '—'}',
                    style: const TextStyle(
                      color: DesertBrewColors.textHint,
                      fontSize: 12,
                    ),
                  ),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        currency.format(
                          (t['total_transfer_price'] as num?)?.toDouble() ?? 0,
                        ),
                        style: const TextStyle(
                          color: DesertBrewColors.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '${(t['quantity'] as num?)?.toStringAsFixed(2) ?? '0.00'} ${t['unit_measure'] ?? ''}',
                        style: const TextStyle(
                          color: DesertBrewColors.textHint,
                          fontSize: 11,
                        ),
                      ),
                    ],
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
