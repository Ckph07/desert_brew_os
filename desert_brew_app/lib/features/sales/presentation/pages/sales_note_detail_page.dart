import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
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
                      onPressed: () => _exportPdf(note.id),
                      icon: const Icon(Icons.picture_as_pdf_rounded),
                      label: const Text('Export PDF'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _exportPng(note.id),
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

  Future<void> _exportPdf(int noteId) async {
    try {
      final bytes = await _repo.exportSalesNotePdf(noteId);
      final note = await _repo.getSalesNote(noteId);
      if (!mounted) return;
      final fileName = 'pedido_${note.noteNumber}.pdf';
      await _saveExportedFile(
        bytes: Uint8List.fromList(bytes),
        defaultFileName: fileName,
        kindLabel: 'PDF',
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error exportando PDF: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _exportPng(int noteId) async {
    try {
      final bytes = await _repo.exportSalesNotePng(noteId);
      final note = await _repo.getSalesNote(noteId);
      if (!mounted) return;
      final fileName = 'pedido_${note.noteNumber}.png';
      await _saveExportedFile(
        bytes: Uint8List.fromList(bytes),
        defaultFileName: fileName,
        kindLabel: 'PNG',
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error exportando PNG: $e'),
          backgroundColor: DesertBrewColors.error,
        ),
      );
    }
  }

  Future<void> _saveExportedFile({
    required Uint8List bytes,
    required String defaultFileName,
    required String kindLabel,
  }) async {
    if (bytes.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('El archivo generado está vacío'),
          backgroundColor: DesertBrewColors.warning,
        ),
      );
      return;
    }

    final destination = await _askDestination(kindLabel);
    if (destination == null || !mounted) return;

    final String? savedPath;
    if (destination == _ExportDestination.downloads) {
      savedPath = await _saveToDownloads(defaultFileName, bytes);
    } else {
      savedPath = await _saveToChosenLocation(defaultFileName, bytes);
    }

    if (!mounted) return;
    if (savedPath == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Exportación cancelada'),
          backgroundColor: DesertBrewColors.warning,
        ),
      );
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Archivo guardado: $savedPath'),
        backgroundColor: DesertBrewColors.success,
      ),
    );
  }

  Future<_ExportDestination?> _askDestination(String kindLabel) async {
    return showModalBottomSheet<_ExportDestination>(
      context: context,
      builder:
          (ctx) => SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  leading: const Icon(Icons.download_rounded),
                  title: Text('Guardar $kindLabel en Descargas'),
                  subtitle: const Text('Ruta automática'),
                  onTap:
                      () => Navigator.of(ctx).pop(_ExportDestination.downloads),
                ),
                ListTile(
                  leading: const Icon(Icons.folder_open_rounded),
                  title: const Text('Elegir ubicación'),
                  subtitle: const Text('Seleccionar carpeta o archivo'),
                  onTap: () => Navigator.of(ctx).pop(_ExportDestination.choose),
                ),
              ],
            ),
          ),
    );
  }

  Future<String?> _saveToDownloads(
    String defaultFileName,
    Uint8List bytes,
  ) async {
    final downloads = await getDownloadsDirectory();
    final fallback = await getApplicationDocumentsDirectory();
    final targetDir = downloads ?? fallback;
    final targetPath = await _buildUniquePath(
      directory: targetDir.path,
      fileName: defaultFileName,
    );
    final file = File(targetPath);
    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  Future<String?> _saveToChosenLocation(
    String defaultFileName,
    Uint8List bytes,
  ) async {
    final ext = defaultFileName.split('.').last.toLowerCase();
    String? pickedPath;
    try {
      pickedPath = await FilePicker.platform.saveFile(
        dialogTitle: 'Guardar archivo',
        fileName: defaultFileName,
        type: FileType.custom,
        allowedExtensions: [ext],
      );
    } catch (_) {
      pickedPath = null;
    }

    if (pickedPath == null) {
      final selectedDir = await FilePicker.platform.getDirectoryPath(
        dialogTitle: 'Selecciona carpeta de destino',
      );
      if (selectedDir == null) return null;
      pickedPath = '$selectedDir${Platform.pathSeparator}$defaultFileName';
    }

    final file = File(pickedPath);
    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  Future<String> _buildUniquePath({
    required String directory,
    required String fileName,
  }) async {
    final dotIndex = fileName.lastIndexOf('.');
    final hasExtension = dotIndex > 0 && dotIndex < fileName.length - 1;
    final base = hasExtension ? fileName.substring(0, dotIndex) : fileName;
    final extension = hasExtension ? fileName.substring(dotIndex) : '';

    var candidate = '$directory${Platform.pathSeparator}$fileName';
    var counter = 1;
    while (await File(candidate).exists()) {
      candidate =
          '$directory${Platform.pathSeparator}$base($counter)$extension';
      counter += 1;
    }
    return candidate;
  }
}

enum _ExportDestination { downloads, choose }
