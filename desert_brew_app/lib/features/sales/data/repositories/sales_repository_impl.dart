import '../../domain/entities/sales_client.dart';
import '../../domain/entities/product.dart';
import '../../domain/entities/sales_note.dart';
import '../../domain/entities/style_liters_summary.dart';
import '../../domain/repositories/sales_repository.dart';
import '../datasources/sales_remote_datasource.dart';
import '../models/sales_client_model.dart';

class SalesRepositoryImpl implements SalesRepository {
  SalesRepositoryImpl(this._remote);
  final SalesRemoteDataSource _remote;

  // ── Clients ───────────────────────────────────────────────────────────────
  @override
  Future<List<SalesClient>> getClients({
    bool activeOnly = true,
    String? search,
  }) => _remote.getClients(activeOnly: activeOnly, search: search);

  @override
  Future<SalesClient> getClient(int id) => _remote.getClient(id);

  @override
  Future<SalesClient> createClient({
    required String businessName,
    required String clientType,
    required String pricingTier,
    String? legalName,
    String? rfc,
    String? email,
    String? phone,
    String? address,
    String? city,
    String? contactPerson,
    double? creditLimit,
    int? maxKegs,
  }) => _remote.createClient(
    SalesClientModel(
      id: 0,
      clientCode: '',
      businessName: businessName,
      clientType: clientType,
      pricingTier: pricingTier,
      currentBalance: 0,
      currentKegs: 0,
      isActive: true,
      legalName: legalName,
      rfc: rfc,
      email: email,
      phone: phone,
      address: address,
      city: city,
      contactPerson: contactPerson,
      creditLimit: creditLimit,
      maxKegs: maxKegs,
    ).toJson(),
  );

  @override
  Future<SalesClient> updateClient(int id, Map<String, dynamic> fields) =>
      _remote.updateClient(id, fields);

  // ── Products ──────────────────────────────────────────────────────────────
  @override
  Future<List<Product>> getProducts({
    bool activeOnly = true,
    String? category,
  }) => _remote.getProducts(activeOnly: activeOnly, category: category);

  @override
  Future<Product> getProduct(int id) => _remote.getProduct(id);

  @override
  Future<Product> createProduct(Map<String, dynamic> fields) =>
      _remote.createProduct(fields);

  @override
  Future<Product> updateProduct(int id, Map<String, dynamic> fields) =>
      _remote.updateProduct(id, fields);

  @override
  Future<void> deleteProduct(int id) => _remote.deleteProduct(id);

  @override
  Future<Map<String, dynamic>> getMarginReport() => _remote.getMarginReport();

  // ── Sales Notes ───────────────────────────────────────────────────────────
  @override
  Future<List<SalesNote>> getSalesNotes({
    String? status,
    String? paymentStatus,
    int? clientId,
    int skip = 0,
    int limit = 50,
  }) => _remote.getSalesNotes(
    status: status,
    paymentStatus: paymentStatus,
    clientId: clientId,
    offset: skip,
    limit: limit,
  );

  @override
  Future<SalesNote> getSalesNote(int id) => _remote.getSalesNote(id);

  @override
  Future<SalesNote> createSalesNote({
    required List<Map<String, dynamic>> items,
    int? clientId,
    String? clientName,
    String channel = 'B2B',
    String paymentMethod = 'TRANSFERENCIA',
    bool includeTaxes = false,
    bool? includeIeps,
    bool? includeIva,
    String? notes,
    String? createdBy,
  }) => _remote.createSalesNote({
    'items': items,
    if (clientId != null) 'client_id': clientId,
    if (clientName != null) 'client_name': clientName,
    'channel': channel,
    'payment_method': paymentMethod,
    'include_taxes': includeTaxes,
    if (includeIeps != null) 'include_ieps': includeIeps,
    if (includeIva != null) 'include_iva': includeIva,
    if (notes != null) 'notes': notes,
    if (createdBy != null) 'created_by': createdBy,
  });

  @override
  Future<SalesNote> updateSalesNote(int id, Map<String, dynamic> fields) =>
      _remote.updateSalesNote(id, fields);

  @override
  Future<SalesNote> confirmSalesNote(int id) => _remote.confirmSalesNote(id);

  @override
  Future<SalesNote> markAsPaid(int id) => _remote.setPaymentStatus(id, 'PAID');

  @override
  Future<void> cancelSalesNote(int id) => _remote.cancelSalesNote(id);

  @override
  Future<void> deleteSalesNote(int id) => _remote.deleteSalesNote(id);

  @override
  Future<List<int>> exportSalesNotePdf(int id) =>
      _remote.exportSalesNotePdf(id);

  @override
  Future<List<int>> exportSalesNotePng(int id) =>
      _remote.exportSalesNotePng(id);

  @override
  Future<StyleLitersSummary> getLitersByStyle({
    String? since,
    String? until,
    String? channel,
  }) => _remote.getLitersByStyle(since: since, until: until, channel: channel);
}
