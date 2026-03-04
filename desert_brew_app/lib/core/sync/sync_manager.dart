import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';

import '../network/connectivity_monitor.dart';
import 'outbox_service.dart';

/// Singleton orchestrator for connectivity and offline queue state.
class SyncManager {
  SyncManager._internal()
    : connectivityMonitor = ConnectivityMonitor(),
      _logger = Logger(printer: PrettyPrinter(methodCount: 0)) {
    outboxService = OutboxService(connectivityMonitor: connectivityMonitor);

    _connectivitySub = connectivityMonitor.onConnectivityChanged.listen((
      online,
    ) {
      isOnlineNotifier.value = online;
    });

    _outboxSub = outboxService.onPendingCountChanged.listen((count) {
      pendingCountNotifier.value = count;
    });
  }

  static final SyncManager instance = SyncManager._internal();

  final ConnectivityMonitor connectivityMonitor;
  late final OutboxService outboxService;

  final Logger _logger;
  StreamSubscription<bool>? _connectivitySub;
  StreamSubscription<int>? _outboxSub;

  final ValueNotifier<bool> isOnlineNotifier = ValueNotifier<bool>(true);
  final ValueNotifier<int> pendingCountNotifier = ValueNotifier<int>(0);

  bool get isOnline => isOnlineNotifier.value;
  int get pendingCount => pendingCountNotifier.value;

  Future<void> initialize() async {
    isOnlineNotifier.value = await connectivityMonitor.checkConnectivity();
    pendingCountNotifier.value = outboxService.pendingCount;
  }

  Future<bool> refreshConnectivity() async {
    final online = await connectivityMonitor.checkConnectivity();
    isOnlineNotifier.value = online;
    return online;
  }

  void enqueueOperation({
    required String method,
    required String path,
    required Future<void> Function() execute,
    String? body,
  }) {
    outboxService.enqueue(
      OutboxEntry(method: method, path: path, execute: execute, body: body),
    );
    pendingCountNotifier.value = outboxService.pendingCount;
  }

  Future<void> flushNow() async {
    await outboxService.flushOutbox();
    pendingCountNotifier.value = outboxService.pendingCount;
  }

  bool shouldQueueOnError(DioException error) {
    return error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout;
  }

  void dispose() {
    _connectivitySub?.cancel();
    _outboxSub?.cancel();
    connectivityMonitor.dispose();
    outboxService.dispose();
    isOnlineNotifier.dispose();
    pendingCountNotifier.dispose();
    _logger.i('SyncManager disposed');
  }
}
