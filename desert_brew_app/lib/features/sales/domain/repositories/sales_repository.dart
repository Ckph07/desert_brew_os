import '../entities/sales_client.dart';
import '../entities/product.dart';
import '../entities/sales_note.dart';
import '../entities/style_liters_summary.dart';

abstract class SalesRepository {
  // ── Clients ────────────────────────────────────────────────────────────
  Future<List<SalesClient>> getClients({
    bool activeOnly = true,
    String? search,
  });
  Future<SalesClient> getClient(int id);
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
  });
  Future<SalesClient> updateClient(int id, Map<String, dynamic> fields);

  // ── Products ────────────────────────────────────────────────────────────
  Future<List<Product>> getProducts({bool activeOnly = true, String? category});
  Future<Product> getProduct(int id);
  Future<Product> createProduct(Map<String, dynamic> fields);
  Future<Product> updateProduct(int id, Map<String, dynamic> fields);
  Future<void> deleteProduct(int id);
  Future<Map<String, dynamic>> getMarginReport();

  // ── Sales Notes ─────────────────────────────────────────────────────────
  Future<List<SalesNote>> getSalesNotes({
    String? status,
    String? paymentStatus,
    int? clientId,
    int skip = 0,
    int limit = 50,
  });
  Future<SalesNote> getSalesNote(int id);
  Future<SalesNote> createSalesNote({
    required List<Map<String, dynamic>> items,
    int? clientId,
    String? clientName,
    String channel,
    String paymentMethod,
    bool includeTaxes,
    String? notes,
    String? createdBy,
  });
  Future<SalesNote> updateSalesNote(int id, Map<String, dynamic> fields);
  Future<SalesNote> confirmSalesNote(int id);
  Future<SalesNote> markAsPaid(int id);
  Future<void> cancelSalesNote(int id);
  Future<void> deleteSalesNote(int id);
  Future<List<int>> exportSalesNotePdf(int id);
  Future<List<int>> exportSalesNotePng(int id);

  // ── Analytics ──────────────────────────────────────────────────────────────
  Future<StyleLitersSummary> getLitersByStyle({
    String? since,
    String? until,
    String? channel,
  });
}
