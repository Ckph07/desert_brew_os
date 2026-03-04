/// Desert Brew OS — API Configuration.
///
/// Maps each microservice to its base URL.
/// Starts with local network (LAN), remote support added later.
class ApiConfig {
  ApiConfig._();

  /// Timeout settings
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 15);

  /// Build base URL for a service
  static String baseUrl(String host, int port) => 'http://$host:$port';
}

/// Service ports matching the backend docker-compose configuration.
enum ServicePort {
  inventory(8001),
  sales(8002),
  security(8003),
  production(8004),
  finance(8005),
  payroll(8006);

  const ServicePort(this.port);
  final int port;
}
