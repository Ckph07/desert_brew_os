import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/config/api_config.dart';
import '../models/sales_client_model.dart';
import '../models/product_model.dart';
import '../models/sales_note_model.dart';
import '../models/style_liters_model.dart';

/// Remote datasource — all HTTP calls to Sales Service on :8002.
class SalesRemoteDataSource {
  SalesRemoteDataSource() : _dio = ApiClient.forService(ServicePort.sales);

  final Dio _dio;

  // ── Clients ──────────────────────────────────────────────────────────────
  Future<List<SalesClientModel>> getClients({
    bool activeOnly = true,
    String? search,
  }) async {
    final response = await _dio.get(
      '/api/v1/sales/clients',
      queryParameters: {
        'active_only': activeOnly,
        if (search != null) 'search': search,
      },
    );
    return (response.data as List)
        .map((e) => SalesClientModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SalesClientModel> getClient(int id) async {
    final response = await _dio.get('/api/v1/sales/clients/$id');
    return SalesClientModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesClientModel> createClient(Map<String, dynamic> payload) async {
    final response = await _dio.post('/api/v1/sales/clients', data: payload);
    return SalesClientModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesClientModel> updateClient(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch(
      '/api/v1/sales/clients/$id',
      data: payload,
    );
    return SalesClientModel.fromJson(response.data as Map<String, dynamic>);
  }

  // ── Products ─────────────────────────────────────────────────────────────
  Future<List<ProductModel>> getProducts({
    bool activeOnly = true,
    String? category,
  }) async {
    final response = await _dio.get(
      '/api/v1/sales/products',
      queryParameters: {
        'active_only': activeOnly,
        if (category != null) 'category': category,
      },
    );
    return (response.data as List)
        .map((e) => ProductModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ProductModel> getProduct(int id) async {
    final response = await _dio.get('/api/v1/sales/products/$id');
    return ProductModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ProductModel> createProduct(Map<String, dynamic> payload) async {
    final response = await _dio.post('/api/v1/sales/products', data: payload);
    return ProductModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ProductModel> updateProduct(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch(
      '/api/v1/sales/products/$id',
      data: payload,
    );
    return ProductModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteProduct(int id) async {
    await _dio.delete('/api/v1/sales/products/$id');
  }

  Future<Map<String, dynamic>> getMarginReport() async {
    final response = await _dio.get('/api/v1/sales/products/margin-report');
    return response.data as Map<String, dynamic>;
  }

  // ── Sales Notes ──────────────────────────────────────────────────────────
  Future<List<SalesNoteModel>> getSalesNotes({
    String? status,
    String? paymentStatus,
    int? clientId,
    int offset = 0,
    int limit = 50,
  }) async {
    final response = await _dio.get(
      '/api/v1/sales/notes',
      queryParameters: {
        if (status != null) 'status': status,
        if (paymentStatus != null) 'payment_status': paymentStatus,
        if (clientId != null) 'client_id': clientId,
        'offset': offset,
        'limit': limit,
      },
    );
    return (response.data as List)
        .map((e) => SalesNoteModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<SalesNoteModel> getSalesNote(int id) async {
    final response = await _dio.get('/api/v1/sales/notes/$id');
    return SalesNoteModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesNoteModel> createSalesNote(Map<String, dynamic> payload) async {
    final response = await _dio.post('/api/v1/sales/notes', data: payload);
    return SalesNoteModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesNoteModel> updateSalesNote(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch('/api/v1/sales/notes/$id', data: payload);
    return SalesNoteModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesNoteModel> confirmSalesNote(int id) async {
    final response = await _dio.patch('/api/v1/sales/notes/$id/confirm');
    return SalesNoteModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesNoteModel> setPaymentStatus(int id, String paymentStatus) async {
    final response = await _dio.patch(
      '/api/v1/sales/notes/$id/payment',
      data: {'payment_status': paymentStatus},
    );
    return SalesNoteModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> cancelSalesNote(int id) async {
    await _dio.patch('/api/v1/sales/notes/$id/cancel');
  }

  Future<void> deleteSalesNote(int id) async {
    await _dio.delete('/api/v1/sales/notes/$id');
  }

  Future<List<int>> exportSalesNotePdf(int id) async {
    final response = await _dio.get<List<int>>(
      '/api/v1/sales/notes/$id/export/pdf',
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data ?? const <int>[];
  }

  Future<List<int>> exportSalesNotePng(int id) async {
    final response = await _dio.get<List<int>>(
      '/api/v1/sales/notes/$id/export/png',
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data ?? const <int>[];
  }

  // ── Analytics ─────────────────────────────────────────────────────────────
  Future<StyleLitersSummaryModel> getLitersByStyle({
    String? since,
    String? until,
    String? channel,
  }) async {
    final response = await _dio.get(
      '/api/v1/sales/notes/analytics/liters-by-style',
      queryParameters: {
        if (since != null) 'since': since,
        if (until != null) 'until': until,
        if (channel != null) 'channel': channel,
      },
    );
    return StyleLitersSummaryModel.fromJson(
      response.data as Map<String, dynamic>,
    );
  }
}
