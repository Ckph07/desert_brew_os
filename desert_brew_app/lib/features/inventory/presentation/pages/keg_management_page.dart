import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/inventory_remote_datasource.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/keg_asset.dart';
import '../bloc/keg/keg_bloc.dart';

// ─ Re-export aliases to avoid ambiguity with KegBlocState ──────────────────
// KegAsset.KegState    → the FSM enum (keg_asset.dart)
// KegBlocState         → BLoC state base class (keg_state.dart via keg_bloc.dart)

class KegManagementPage extends StatefulWidget {
  const KegManagementPage({super.key});

  @override
  State<KegManagementPage> createState() => _KegManagementPageState();
}

class _KegManagementPageState extends State<KegManagementPage> {
  String? _stateFilter;

  static const _kegStates = <String?>[
    null, 'EMPTY', 'CLEAN', 'FULL', 'DELIVERED', 'IN_CLIENT', 'RETURNED', 'CLEANING', 'MAINTENANCE'
  ];
  static const _kegLabels = [
    'Todos', 'Vacío', 'Limpio', 'Lleno', 'Entregado', 'En Cliente', 'Devuelto', 'Limpiando', 'Mant.'
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => KegBloc(
        InventoryRepositoryImpl(InventoryRemoteDataSource()),
      )..add(KegLoadRequested(stateFilter: _stateFilter)),
      child: Builder(builder: (ctx) => _buildBody(ctx)),
    );
  }

  Widget _buildBody(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Barriles (Kegs)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => context
                .read<KegBloc>()
                .add(KegLoadRequested(stateFilter: _stateFilter)),
          ),
        ],
      ),
      body: Column(
        children: [
          // ── State filter ───────────────────────────────────────────
          SizedBox(
            height: 44,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _kegStates.length,
              itemBuilder: (_, i) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  label: Text(_kegLabels[i],
                      style: const TextStyle(fontSize: 11)),
                  selected: _stateFilter == _kegStates[i],
                  onSelected: (_) {
                    setState(() => _stateFilter = _kegStates[i]);
                    context
                        .read<KegBloc>()
                        .add(KegLoadRequested(stateFilter: _kegStates[i]));
                  },
                  selectedColor:
                      DesertBrewColors.primary.withValues(alpha: 0.2),
                ),
              ),
            ),
          ),

          // ── Stats Bar ──────────────────────────────────────────────
          BlocBuilder<KegBloc, KegBlocState>(
            builder: (_, state) {
              if (state is! KegLoaded) return const SizedBox.shrink();
              final kegs = state.kegs;
              final full = kegs.where((k) => k.currentState == KegState.full).length;
              final inClient = kegs.where((k) => k.currentState == KegState.inClient).length;
              final available = kegs.where((k) => k.isAvailable).length;
              final maintenance = kegs.where((k) =>
                  k.currentState == KegState.maintenance || k.needsMaintenance).length;
              return Container(
                margin: const EdgeInsets.all(12),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: DesertBrewColors.surface,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    _StatCell('${kegs.length}', 'Total', DesertBrewColors.textHint),
                    _StatCell('$available', 'Disponibles', DesertBrewColors.success),
                    _StatCell('$full', 'Llenos', DesertBrewColors.primary),
                    _StatCell('$inClient', 'En Cliente', DesertBrewColors.warning),
                    _StatCell('$maintenance', 'Mant.', DesertBrewColors.error),
                  ],
                ),
              );
            },
          ),

          // ── Keg List ───────────────────────────────────────────────
          Expanded(
            child: BlocBuilder<KegBloc, KegBlocState>(
              builder: (context, state) {
                if (state is KegLoading || state is KegInitial) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is KegError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.wifi_off_rounded,
                            size: 48, color: DesertBrewColors.error),
                        const SizedBox(height: 12),
                        Text(state.message,
                            style: const TextStyle(
                                color: DesertBrewColors.textHint, fontSize: 12),
                            textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () =>
                              context.read<KegBloc>().add(KegLoadRequested()),
                          child: const Text('Reintentar'),
                        ),
                      ],
                    ),
                  );
                }
                if (state is KegLoaded) {
                  if (state.kegs.isEmpty) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.sports_bar_rounded,
                              size: 56, color: DesertBrewColors.textHint),
                          SizedBox(height: 12),
                          Text('Sin barriles registrados',
                              style: TextStyle(
                                  color: DesertBrewColors.textSecondary)),
                        ],
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
                    itemCount: state.kegs.length,
                    itemBuilder: (ctx, i) => _KegTile(
                        keg: state.kegs[i],
                        bloc: context.read<KegBloc>()),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

Color _kegStateColor(KegState s) {
  if (s == KegState.clean) return DesertBrewColors.success;
  if (s == KegState.full) return DesertBrewColors.primary;
  if (s == KegState.delivered || s == KegState.inClient) return DesertBrewColors.warning;
  if (s == KegState.maintenance) return DesertBrewColors.error;
  if (s == KegState.cleaning) return const Color(0xFF3B82F6);
  if (s == KegState.returned) return const Color(0xFF8B5CF6);
  return DesertBrewColors.textHint; // empty
}

IconData _kegStateIcon(KegState s) {
  if (s == KegState.cleaning) return Icons.cleaning_services_rounded;
  if (s == KegState.clean) return Icons.check_circle_outline_rounded;
  if (s == KegState.full) return Icons.sports_bar_rounded;
  if (s == KegState.delivered) return Icons.local_shipping_rounded;
  if (s == KegState.inClient) return Icons.person_rounded;
  if (s == KegState.returned) return Icons.assignment_return_rounded;
  if (s == KegState.maintenance) return Icons.build_rounded;
  return Icons.sports_bar_outlined; // empty
}

List<String> _kegNextStates(KegState s) {
  if (s == KegState.empty) return ['CLEANING', 'MAINTENANCE'];
  if (s == KegState.cleaning) return ['CLEAN'];
  if (s == KegState.clean) return ['FULL', 'MAINTENANCE'];
  if (s == KegState.full) return ['DELIVERED', 'EMPTY'];
  if (s == KegState.delivered) return ['IN_CLIENT'];
  if (s == KegState.inClient) return ['RETURNED'];
  if (s == KegState.returned) return ['CLEANING', 'EMPTY'];
  if (s == KegState.maintenance) return ['EMPTY', 'CLEAN'];
  return [];
}

// ─── KegTile ─────────────────────────────────────────────────────────────────

class _KegTile extends StatelessWidget {
  const _KegTile({required this.keg, required this.bloc});
  final KegAsset keg;
  final KegBloc bloc;

  void _showTransitionMenu(BuildContext context) {
    final states = _kegNextStates(keg.currentState);
    if (states.isEmpty) return;
    showModalBottomSheet(
      context: context,
      backgroundColor: DesertBrewColors.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Barril ${keg.serialNumber}',
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 4),
            Text('Estado actual: ${keg.currentState.displayName}',
                style: const TextStyle(
                    color: DesertBrewColors.textHint, fontSize: 12)),
            const SizedBox(height: 16),
            ...states.map((s) => ListTile(
                  leading: const Icon(Icons.arrow_forward_rounded,
                      color: DesertBrewColors.primary),
                  title: Text(KegState.fromString(s).displayName),
                  onTap: () {
                    Navigator.pop(context);
                    bloc.add(KegTransitionRequested(
                      kegId: keg.id,
                      newState: s,
                      userId: 1,
                    ));
                  },
                )),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('dd/MM/yy');
    final stateColor = _kegStateColor(keg.currentState);
    final stateIcon = _kegStateIcon(keg.currentState);
    return GestureDetector(
      onTap: () => _showTransitionMenu(context),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: DesertBrewColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: stateColor.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: stateColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(stateIcon, color: stateColor, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(keg.serialNumber,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 13)),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: stateColor.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(keg.currentState.displayName,
                            style: TextStyle(
                                color: stateColor,
                                fontSize: 10,
                                fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${keg.sizeLiters}L · ${keg.kegType} · #${keg.cycleCount} ciclos',
                    style: const TextStyle(
                        color: DesertBrewColors.textHint, fontSize: 11),
                  ),
                  if (keg.currentLocation != null)
                    Text(keg.currentLocation!,
                        style: const TextStyle(
                            color: DesertBrewColors.textHint, fontSize: 11)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (keg.needsMaintenance)
                  const Icon(Icons.warning_amber_rounded,
                      color: DesertBrewColors.warning, size: 16),
                if (keg.lastFilledAt != null)
                  Text(
                    'Llenado: ${fmt.format(keg.lastFilledAt!)}',
                    style: const TextStyle(
                        color: DesertBrewColors.textHint, fontSize: 10),
                  ),
                const Icon(Icons.chevron_right_rounded,
                    color: DesertBrewColors.textHint, size: 18),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatCell extends StatelessWidget {
  const _StatCell(this.value, this.label, this.color);
  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(value,
              style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                  fontSize: 18)),
          Text(label,
              style: const TextStyle(
                  color: DesertBrewColors.textHint, fontSize: 9),
              textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
