/// All shared enums mirroring the backend Python enums.
///
/// These are the single source of truth for enum values in Flutter,
/// directly mapped from the backend service models.

// ===== Inventory Service Enums =====

/// Ingredient categories for raw material stock.
enum IngredientCategory {
  malt('MALT'),
  hops('HOPS'),
  yeast('YEAST'),
  bottle('BOTTLE'),
  cap('CAP'),
  chemical('CHEMICAL'),
  label('LABEL'),
  other('OTHER');

  const IngredientCategory(this.value);
  final String value;

  static IngredientCategory fromString(String s) =>
      values.firstWhere((e) => e.value == s.toUpperCase());
}

/// Unit of measure for inventory quantities.
enum UnitMeasure {
  kg('KG'),
  g('G'),
  l('L'),
  ml('ML'),
  unit('UNIT');

  const UnitMeasure(this.value);
  final String value;

  static UnitMeasure fromString(String s) =>
      values.firstWhere((e) => e.value == s.toUpperCase());
}

/// Who produces the product (critical for Transfer Pricing).
enum OriginType {
  house('house', 'Producción propia'),
  guest('guest', 'Cerveza invitada'),
  commercial('commercial', 'Cerveza comercial'),
  merchandise('merchandise', 'Merchandising');

  const OriginType(this.value, this.displayName);
  final String value;
  final String displayName;

  static OriginType fromString(String s) =>
      values.firstWhere((e) => e.value == s.toLowerCase());
}

/// Type of finished product.
enum ProductType {
  ownProduction('OWN_PRODUCTION', 'Producción Propia'),
  commercial('COMMERCIAL', 'Comercial'),
  guestCraft('GUEST_CRAFT', 'Cerveza Invitada'),
  merchandise('MERCHANDISE', 'Merchandising');

  const ProductType(this.value, this.displayName);
  final String value;
  final String displayName;

  static ProductType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Product category / packaging format.
enum ProductCategory {
  beerKeg('BEER_KEG', '🍺 Barril'),
  beerBottle('BEER_BOTTLE', '🍺 Botella'),
  beerCan('BEER_CAN', '🍺 Lata'),
  waterBottle('WATER_BOTTLE', '💧 Botella Agua'),
  waterJug('WATER_JUG', '💧 Garrafón'),
  merchCap('MERCH_CAP', '🧢 Cachucha'),
  merchShirt('MERCH_SHIRT', '👕 Playera'),
  merchGlass('MERCH_GLASS', '🥃 Vaso'),
  merchGrowler('MERCH_GROWLER', '🍺 Growler'),
  merchOther('MERCH_OTHER', '📦 Otro');

  const ProductCategory(this.value, this.displayName);
  final String value;
  final String displayName;

  static ProductCategory fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Availability status of finished products.
enum AvailabilityStatus {
  available('AVAILABLE'),
  reserved('RESERVED'),
  sold('SOLD'),
  damaged('DAMAGED'),
  expired('EXPIRED');

  const AvailabilityStatus(this.value);
  final String value;

  static AvailabilityStatus fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Product movement types.
enum MovementType {
  production('PRODUCTION'),
  purchase('PURCHASE'),
  sale('SALE'),
  transfer('TRANSFER'),
  adjustment('ADJUSTMENT'),
  damage('DAMAGE'),
  expiration('EXPIRATION'),
  returnMovement('RETURN');

  const MovementType(this.value);
  final String value;

  static MovementType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Cold room locations.
enum ColdRoomLocation {
  coldRoomA('COLD_ROOM_A', 'Cuarto Frío A'),
  coldRoomB('COLD_ROOM_B', 'Cuarto Frío B'),
  taproomCooler('TAPROOM_COOLER', 'Refrigerador Taproom'),
  warehouse('WAREHOUSE', 'Almacén');

  const ColdRoomLocation(this.value, this.displayName);
  final String value;
  final String displayName;

  static ColdRoomLocation fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

// ===== Keg Asset Enums =====

/// 10-state FSM for keg lifecycle.
enum KegState {
  empty('EMPTY', '⬜ Vacío'),
  dirty('DIRTY', '🟤 Sucio'),
  clean('CLEAN', '🔵 Limpio'),
  filling('FILLING', '🟡 Llenando'),
  full('FULL', '🟢 Lleno'),
  tapped('TAPPED', '🟠 En Grifo'),
  inClient('IN_CLIENT', '🔴 En Cliente'),
  inTransit('IN_TRANSIT', '🚚 En Tránsito'),
  quarantine('QUARANTINE', '🟣 Cuarentena'),
  retired('RETIRED', '⚫ Retirado');

  const KegState(this.value, this.displayName);
  final String value;
  final String displayName;

  static KegState fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Keg connection types.
enum KegType {
  sankeD('SANKE_D'),
  sankeS('SANKE_S'),
  cornelius('CORNELIUS'),
  other('OTHER');

  const KegType(this.value);
  final String value;

  static KegType fromString(String s) => values.firstWhere((e) => e.value == s);
}

/// Keg ownership.
enum KegOwnership {
  own('OWN'),
  guestBrewery('GUEST_BREWERY'),
  rented('RENTED');

  const KegOwnership(this.value);
  final String value;

  static KegOwnership fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

// ===== Production Service Enums =====

/// 6-state production batch lifecycle.
enum BatchStatus {
  planned('PLANNED', '📋 Planeado'),
  brewing('BREWING', '🔥 Cocción'),
  fermenting('FERMENTING', '🧪 Fermentando'),
  conditioning('CONDITIONING', '❄️ Maduración'),
  packaging('PACKAGING', '📦 Empaque'),
  completed('COMPLETED', '✅ Completado');

  const BatchStatus(this.value, this.displayName);
  final String value;
  final String displayName;

  static BatchStatus fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Ingredient price categories.
enum IngredientPriceCategory {
  malt('MALT'),
  hop('HOP'),
  yeast('YEAST'),
  adjunct('ADJUNCT'),
  chemical('CHEMICAL'),
  packaging('PACKAGING'),
  other('OTHER');

  const IngredientPriceCategory(this.value);
  final String value;

  static IngredientPriceCategory fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Fixed cost categories.
enum FixedCostCategory {
  fuel('FUEL'),
  energy('ENERGY'),
  water('WATER'),
  hr('HR'),
  operations('OPERATIONS'),
  gasCo2('GAS_CO2'),
  comms('COMMS'),
  vehicle('VEHICLE'),
  other('OTHER');

  const FixedCostCategory(this.value);
  final String value;

  static FixedCostCategory fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

// ===== Sales Service Enums =====

/// Client types.
enum ClientType {
  b2b('B2B'),
  b2c('B2C'),
  distributor('DISTRIBUTOR');

  const ClientType(this.value);
  final String value;

  static ClientType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Pricing tiers for clients.
enum PricingTier {
  platinum('PLATINUM'),
  gold('GOLD'),
  silver('SILVER'),
  retail('RETAIL');

  const PricingTier(this.value);
  final String value;

  static PricingTier fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Sales note lifecycle status.
enum SalesNoteStatus {
  draft('DRAFT'),
  confirmed('CONFIRMED'),
  cancelled('CANCELLED');

  const SalesNoteStatus(this.value);
  final String value;

  static SalesNoteStatus fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Sales channels.
enum SalesChannel {
  b2b('B2B'),
  taproom('TAPROOM'),
  ecommerce('ECOMMERCE');

  const SalesChannel(this.value);
  final String value;

  static SalesChannel fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Payment methods.
enum PaymentMethod {
  transferencia('TRANSFERENCIA'),
  efectivo('EFECTIVO'),
  tarjeta('TARJETA');

  const PaymentMethod(this.value);
  final String value;

  static PaymentMethod fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

// ===== Security Service Enums =====

/// Device enrollment status.
enum DeviceStatus {
  pending('pending'),
  active('active'),
  revoked('revoked'),
  suspended('suspended');

  const DeviceStatus(this.value);
  final String value;

  static DeviceStatus fromString(String s) =>
      values.firstWhere((e) => e.value.toLowerCase() == s.toLowerCase());
}
// ===== Finance Service Enums (Sprint 3.5b) =====

/// Income types.
enum IncomeType {
  salesNote('sales_note', 'Nota de Venta'),
  cashSale('cash_sale', 'Venta en Efectivo'),
  b2bInvoice('b2b_invoice', 'Factura B2B'),
  other('other', 'Otro');

  const IncomeType(this.value, this.displayName);
  final String value;
  final String displayName;

  static IncomeType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Income categories.
enum IncomeCategory {
  beerSales('beer_sales', '🍺 Cerveza'),
  merchSales('merch_sales', '👕 Merchandising'),
  foodSales('food_sales', '🍔 Alimentos'),
  event('event', '🎉 Eventos'),
  other('other', '📦 Otro');

  const IncomeCategory(this.value, this.displayName);
  final String value;
  final String displayName;

  static IncomeCategory fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Expense types.
enum ExpenseType {
  supplierPayment('supplier_payment', 'Pago a Proveedor'),
  payroll('payroll', 'Nómina'),
  purchase('purchase', 'Compra'),
  utility('utility', 'Servicio'),
  rent('rent', 'Renta'),
  tax('tax', 'Impuesto'),
  maintenance('maintenance', 'Mantenimiento'),
  other('other', 'Otro');

  const ExpenseType(this.value, this.displayName);
  final String value;
  final String displayName;

  static ExpenseType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Expense categories.
enum ExpenseCategory {
  rawMaterials('raw_materials', 'Materia Prima'),
  packaging('packaging', 'Empaque'),
  payroll('payroll', 'Nómina'),
  energy('energy', 'Energía'),
  water('water', 'Agua'),
  gas('gas', 'Gas'),
  rent('rent', 'Renta'),
  maintenance('maintenance', 'Mantenimiento'),
  transport('transport', 'Transporte'),
  marketing('marketing', 'Marketing'),
  communications('communications', 'Comunicaciones'),
  taxes('taxes', 'Impuestos'),
  other('other', 'Otro');

  const ExpenseCategory(this.value, this.displayName);
  final String value;
  final String displayName;

  static ExpenseCategory fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Financial profit centers.
enum FinanceProfitCenter {
  factory('factory', '🏭 Fábrica'),
  taproom('taproom', '🍺 Taproom'),
  distribution('distribution', '🚚 Distribución'),
  general('general', '📊 General');

  const FinanceProfitCenter(this.value, this.displayName);
  final String value;
  final String displayName;

  static FinanceProfitCenter fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

// ===== Payroll Enums =====

/// Employment type.
enum EmploymentType {
  fixed('FIXED'),
  temporary('TEMPORARY');

  const EmploymentType(this.value);
  final String value;

  static EmploymentType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Payroll period type.
enum PayrollPeriodType {
  daily('DAILY'),
  weekly('WEEKLY'),
  biweekly('BIWEEKLY'),
  monthly('MONTHLY');

  const PayrollPeriodType(this.value);
  final String value;

  static PayrollPeriodType fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}

/// Department.
enum Department {
  production('PRODUCTION'),
  taproom('TAPROOM'),
  logistics('LOGISTICS'),
  admin('ADMIN');

  const Department(this.value);
  final String value;

  static Department fromString(String s) =>
      values.firstWhere((e) => e.value == s);
}
