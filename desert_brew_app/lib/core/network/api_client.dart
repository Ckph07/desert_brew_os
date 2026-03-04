import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import '../config/api_config.dart';
import '../config/app_config.dart';

/// Centralized API client using Dio with interceptors.
///
/// Each microservice gets its own [Dio] instance via [forService],
/// sharing the same interceptors (logging, error handling, auth).
class ApiClient {
  ApiClient._();

  static final Logger _logger = Logger(
    printer: PrettyPrinter(methodCount: 0),
  );

  /// Create a Dio instance configured for a specific service.
  static Dio forService(ServicePort service) {
    final baseUrl = ApiConfig.baseUrl(AppConfig.backendHost, service.port);

    final dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: ApiConfig.connectTimeout,
        receiveTimeout: ApiConfig.receiveTimeout,
        sendTimeout: ApiConfig.sendTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Logging interceptor
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          _logger.d('→ ${options.method} ${options.uri}');
          handler.next(options);
        },
        onResponse: (response, handler) {
          _logger.d(
            '← ${response.statusCode} ${response.requestOptions.uri}',
          );
          handler.next(response);
        },
        onError: (error, handler) {
          _logger.e(
            '✖ ${error.requestOptions.method} ${error.requestOptions.uri}',
            error: error.response?.data ?? error.message,
          );
          handler.next(error);
        },
      ),
    );

    return dio;
  }

  /// Convenience getters for each service.
  static Dio get inventory => forService(ServicePort.inventory);
  static Dio get sales => forService(ServicePort.sales);
  static Dio get security => forService(ServicePort.security);
  static Dio get production => forService(ServicePort.production);
  static Dio get finance => forService(ServicePort.finance);
  static Dio get payroll => forService(ServicePort.payroll);
}
