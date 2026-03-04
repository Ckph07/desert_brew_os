/// Desert Brew OS — App-wide configuration.
///
/// Feature flags, environment detection, and app constants.
class AppConfig {
  AppConfig._();

  static const String appName = 'Desert Brew OS';
  static const String version = '0.1.0';
  static const String companyName = 'Desert Brew Co.';
  static const String companyCity = 'Saltillo, Coahuila';

  /// Backend host for development.
  /// - 'localhost' for Flutter Web (Chrome on same machine as backend)
  /// - '192.168.1.100' for physical iOS/Android on the brewery LAN
  static String backendHost = 'localhost';

  /// Feature flags
  static bool enableOfflineMode = true;
  static bool enableCryptoSigning = true;
  static bool enableInventoryDeduction = true;
}

/// User roles for role-based access control.
enum UserRole {
  admin('Admin', 'Full system access'),
  brewmaster('Brewmaster', 'Production & recipes'),
  warehouseManager('Warehouse Manager', 'Inventory & cold rooms'),
  salesRep('Sales Rep', 'Clients, notes & deliveries'),
  bartender('Bartender', 'Taproom POS & tips'),
  b2bClient('B2B Client', 'View orders & delivery status');

  const UserRole(this.displayName, this.description);
  final String displayName;
  final String description;
}
