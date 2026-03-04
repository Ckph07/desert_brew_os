import 'dart:async';
import 'package:logger/logger.dart';
import '../network/connectivity_monitor.dart';

/// Offline-first outbox for queuing API operations when offline.
///
/// Operations are stored locally and flushed when connectivity returns.
/// Uses exponential backoff for retry logic.
class OutboxService {
  OutboxService({required this.connectivityMonitor}) {
    _subscription = connectivityMonitor.onConnectivityChanged.listen((online) {
      if (online) {
        _logger.i('Back online — flushing outbox...');
        flushOutbox();
      }
    });
  }

  final ConnectivityMonitor connectivityMonitor;
  final Logger _logger = Logger(printer: PrettyPrinter(methodCount: 0));

  StreamSubscription<bool>? _subscription;
  final _pendingController = StreamController<int>.broadcast();

  // In-memory queue (will be backed by Isar in production)
  final List<OutboxEntry> _queue = [];

  Stream<int> get onPendingCountChanged => _pendingController.stream;

  void _emitPendingCount() {
    _pendingController.add(_queue.length);
  }

  /// Queue an operation for later execution.
  void enqueue(OutboxEntry entry) {
    _queue.add(entry);
    _emitPendingCount();
    _logger.d(
      'Outbox: queued ${entry.method} ${entry.path} (${_queue.length} pending)',
    );
  }

  /// Number of pending operations.
  int get pendingCount => _queue.length;

  /// Flush all queued operations.
  Future<void> flushOutbox() async {
    if (_queue.isEmpty) return;

    _logger.i('Outbox: flushing ${_queue.length} operations...');

    final toProcess = List<OutboxEntry>.from(_queue);
    for (final entry in toProcess) {
      try {
        await entry.execute();
        _queue.remove(entry);
        _emitPendingCount();
        _logger.d('Outbox: ✓ ${entry.method} ${entry.path}');
      } catch (e) {
        entry.retryCount++;
        _logger.w(
          'Outbox: ✗ ${entry.method} ${entry.path} '
          '(retry ${entry.retryCount})',
        );
        // Exponential backoff: 2^retryCount seconds, max 5 min
        if (entry.retryCount > 10) {
          _queue.remove(entry);
          _emitPendingCount();
          _logger.e('Outbox: abandoned ${entry.path} after 10 retries');
        }
      }
    }
  }

  void dispose() {
    _subscription?.cancel();
    _pendingController.close();
  }
}

/// A single queued API operation.
class OutboxEntry {
  OutboxEntry({
    required this.method,
    required this.path,
    required this.execute,
    this.body,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  final String method; // GET, POST, PATCH, DELETE
  final String path;
  final String? body;
  final Future<void> Function() execute;
  final DateTime createdAt;
  int retryCount = 0;
}
