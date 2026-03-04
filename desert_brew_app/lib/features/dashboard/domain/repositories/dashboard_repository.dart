import '../entities/global_kpi_snapshot.dart';

abstract class DashboardRepository {
  Future<GlobalKpiSnapshot> getGlobalKpis({bool allowStaleFallback = true});
}
