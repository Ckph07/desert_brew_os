import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/sales_remote_datasource.dart';
import '../../data/repositories/sales_repository_impl.dart';
import '../../domain/entities/sales_note.dart';

class SalesNoteDetailPage extends StatefulWidget {
  const SalesNoteDetailPage({super.key, required this.noteId});
  final int noteId;

  @override
  State<SalesNoteDetailPage> createState() => _SalesNoteDetailPageState();
}

class _SalesNoteDetailPageState extends State<SalesNoteDetailPage> {
  final _repo = SalesRepositoryImpl(SalesRemoteDataSource());
  late Future<SalesNote> _future;

  @override
  void initState() {
    super.initState();
    _future = _repo.getSalesNote(widget.noteId);
  }

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalle de Nota'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () => setState(() {
                  _future = _repo.getSalesNote(widget.noteId);
                }),
          ),
        ],
      ),
      body: FutureBuilder<SalesNote>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData) {
            return Center(
              child: Text(
                snapshot.error?.toString() ?? 'No se pudo cargar la nota',
                style: const TextStyle(color: DesertBrewColors.error),
              ),
            );
          }
          final note = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                note.noteNumber,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 22,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                note.clientName ?? 'Sin cliente',
                style: const TextStyle(color: DesertBrewColors.textHint),
              ),
              const SizedBox(height: 10),
              Text(
                'Estado: ${note.status} · Pago: ${note.paymentStatus}',
                style: const TextStyle(color: DesertBrewColors.textSecondary),
              ),
              const SizedBox(height: 10),
              Text(
                'Total: ${currency.format(note.total)}',
                style: const TextStyle(
                  color: DesertBrewColors.primary,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Items',
                style: TextStyle(
                  color: DesertBrewColors.textSecondary,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              ...note.items.map(
                (item) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(item.productName),
                    subtitle: Text(
                      '${item.quantity.toStringAsFixed(2)} ${item.unitMeasure} · ${item.sku ?? 'SIN-SKU'}',
                      style: const TextStyle(fontSize: 12),
                    ),
                    trailing: Text(
                      currency.format(item.lineTotal),
                      style: const TextStyle(
                        color: DesertBrewColors.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _exportPdf(context, note.id),
                      icon: const Icon(Icons.picture_as_pdf_rounded),
                      label: const Text('Export PDF'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _exportPng(context, note.id),
                      icon: const Icon(Icons.image_rounded),
                      label: const Text('Export PNG'),
                    ),
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _exportPdf(BuildContext context, int noteId) async {
    try {
      final bytes = await _repo.exportSalesNotePdf(noteId);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('PDF generado (${bytes.length} bytes)'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error exportando PDF: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _exportPng(BuildContext context, int noteId) async {
    try {
      final bytes = await _repo.exportSalesNotePng(noteId);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('PNG generado (${bytes.length} bytes)'),
          backgroundColor: DesertBrewColors.success,
        ),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error exportando PNG: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }
}
