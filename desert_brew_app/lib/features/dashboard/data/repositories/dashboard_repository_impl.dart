import '../../domain/entities/global_kpi_snapshot.dart';
import '../../domain/repositories/dashboard_repository.dart';
import '../datasources/dashboard_remote_datasource.dart';

class DashboardRepositoryImpl implements DashboardRepository {
  DashboardRepositoryImpl(this._remote);

  final DashboardRemoteDataSource _remote;
  GlobalKpiSnapshot? _cachedSnapshot;

  @override
  Future<GlobalKpiSnapshot> getGlobalKpis({
    bool allowStaleFallback = true,
  }) async {
    try {
      final fresh = await _remote.fetchGlobalKpis();
      _cachedSnapshot = fresh;
      return fresh;
    } catch (_) {
      if (allowStaleFallback && _cachedSnapshot != null) {
        return _cachedSnapshot!.markAsStale();
      }
      rethrow;
    }
  }
}
