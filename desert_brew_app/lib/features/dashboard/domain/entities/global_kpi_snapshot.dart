import 'package:equatable/equatable.dart';

class GlobalKpiSnapshot extends Equatable {
  const GlobalKpiSnapshot({
    required this.inventoryValueMxn,
    required this.activeBatches,
    required this.monthlySalesNotes,
    required this.kegsInClient,
    required this.pendingPayrollEntries,
    required this.activeDevices,
    required this.fetchedAt,
    this.isStale = false,
  });

  final double inventoryValueMxn;
  final int activeBatches;
  final int monthlySalesNotes;
  final int kegsInClient;
  final int pendingPayrollEntries;
  final int activeDevices;
  final DateTime fetchedAt;
  final bool isStale;

  GlobalKpiSnapshot markAsStale() {
    return GlobalKpiSnapshot(
      inventoryValueMxn: inventoryValueMxn,
      activeBatches: activeBatches,
      monthlySalesNotes: monthlySalesNotes,
      kegsInClient: kegsInClient,
      pendingPayrollEntries: pendingPayrollEntries,
      activeDevices: activeDevices,
      fetchedAt: fetchedAt,
      isStale: true,
    );
  }

  @override
  List<Object?> get props => [
    inventoryValueMxn,
    activeBatches,
    monthlySalesNotes,
    kegsInClient,
    pendingPayrollEntries,
    activeDevices,
    fetchedAt,
    isStale,
  ];
}
