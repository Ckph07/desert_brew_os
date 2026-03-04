import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:logger/logger.dart';

/// Monitors network connectivity and exposes stream + sync check.
///
/// Used by the Outbox/Sync system to decide when to flush queued ops.
class ConnectivityMonitor {
  ConnectivityMonitor() {
    _subscription = Connectivity().onConnectivityChanged.listen(_update);
  }

  final Logger _logger = Logger(
    printer: PrettyPrinter(methodCount: 0),
  );

  StreamSubscription<List<ConnectivityResult>>? _subscription;
  final _controller = StreamController<bool>.broadcast();

  bool _isConnected = true;
  bool get isConnected => _isConnected;
  Stream<bool> get onConnectivityChanged => _controller.stream;

  void _update(List<ConnectivityResult> results) {
    final connected = results.any(
      (r) => r != ConnectivityResult.none,
    );

    if (connected != _isConnected) {
      _isConnected = connected;
      _controller.add(connected);
      _logger.i('Connectivity: ${connected ? "ONLINE ✓" : "OFFLINE ✗"}');
    }
  }

  /// Check current connectivity status.
  Future<bool> checkConnectivity() async {
    final results = await Connectivity().checkConnectivity();
    _isConnected = results.any((r) => r != ConnectivityResult.none);
    return _isConnected;
  }

  void dispose() {
    _subscription?.cancel();
    _controller.close();
  }
}
