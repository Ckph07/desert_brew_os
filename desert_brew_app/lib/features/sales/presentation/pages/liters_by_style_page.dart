import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/sales_remote_datasource.dart';
import '../../data/repositories/sales_repository_impl.dart';
import '../../domain/entities/style_liters_summary.dart';
import '../bloc/analytics/liters_by_style_bloc.dart';

/// Horizontal bar-chart: Litros vendidos por estilo de cerveza
class LitersByStylePage extends StatefulWidget {
  const LitersByStylePage({super.key});

  @override
  State<LitersByStylePage> createState() => _LitersByStylePageState();
}

class _LitersByStylePageState extends State<LitersByStylePage> {
  // filters
  String? _since;
  String? _until;
  String? _channel;

  static const _channels = [
    null,
    'B2B',
    'B2C',
    'TAPROOM',
    'DISTRIBUTOR',
  ];

  static const _channelLabels = [
    'Todos',
    'B2B',
    'B2C',
    'Taproom',
    'Distribuidor',
  ];

  // Pretty palette — each style gets a distinct warm/brewery color
  static const _barColors = [
    Color(0xFFF59E0B), // amber
    Color(0xFF10B981), // emerald
    Color(0xFF3B82F6), // blue
    Color(0xFFF97316), // orange
    Color(0xFF8B5CF6), // violet
    Color(0xFFEC4899), // pink
    Color(0xFF06B6D4), // cyan
    Color(0xFFEF4444), // red
    Color(0xFF84CC16), // lime
    Color(0xFF6366F1), // indigo
  ];

  Color _colorFor(int index) =>
      _barColors[index % _barColors.length];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => LitersByStyleBloc(
        SalesRepositoryImpl(SalesRemoteDataSource()),
      )..add(LitersByStyleLoadRequested(
          since: _since, until: _until, channel: _channel)),
      child: _buildScaffold(),
    );
  }

  Widget _buildScaffold() {
    return Builder(
      builder: (context) => Scaffold(
        appBar: AppBar(
          title: const Text('Litros × Estilo'),
          actions: [
            IconButton(
              icon: const Icon(Icons.tune_rounded),
              tooltip: 'Filtros',
              onPressed: () => _showFiltersSheet(context),
            ),
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              onPressed: () => context
                  .read<LitersByStyleBloc>()
                  .add(LitersByStyleLoadRequested(
                      since: _since, until: _until, channel: _channel)),
            ),
          ],
        ),
        body: BlocBuilder<LitersByStyleBloc, LitersByStyleState>(
          builder: (context, state) {
            if (state is LitersByStyleLoading ||
                state is LitersByStyleInitial) {
              return const Center(child: CircularProgressIndicator());
            }
            if (state is LitersByStyleError) {
              return _Error(
                message: state.message,
                onRetry: () => context
                    .read<LitersByStyleBloc>()
                    .add(LitersByStyleLoadRequested()),
              );
            }
            if (state is LitersByStyleLoaded) {
              final s = state.summary;
              if (s.styles.isEmpty) {
                return _Empty(
                  hasFilters: _since != null || _channel != null,
                  onClear: () => setState(() {
                    _since = _until = _channel = null;
                  }),
                );
              }
              return _AnalyticsBody(
                summary: s,
                colorFor: _colorFor,
                since: _since,
                until: _until,
                channel: _channel,
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }

  void _showFiltersSheet(BuildContext ctx) {
    String? tmpSince = _since;
    String? tmpUntil = _until;
    String? tmpChannel = _channel;

    showModalBottomSheet(
      context: ctx,
      isScrollControlled: true,
      backgroundColor: DesertBrewColors.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (sheetCtx) => StatefulBuilder(
        builder: (sheetCtx, setSt) => Padding(
          padding: EdgeInsets.fromLTRB(
              20, 12, 20,
              MediaQuery.of(sheetCtx).viewInsets.bottom + 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  decoration: BoxDecoration(
                    color: DesertBrewColors.textHint,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text('Filtros',
                  style: TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 16),

              // Channel selector
              const Text('Canal',
                  style: TextStyle(
                      color: DesertBrewColors.textHint, fontSize: 12)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: List.generate(_channels.length, (i) {
                  return ChoiceChip(
                    label: Text(_channelLabels[i]),
                    selected: tmpChannel == _channels[i],
                    onSelected: (_) =>
                        setSt(() => tmpChannel = _channels[i]),
                    selectedColor: DesertBrewColors.primary
                        .withValues(alpha: 0.2),
                  );
                }),
              ),
              const SizedBox(height: 16),

              // Date range
              Row(
                children: [
                  Expanded(
                    child: _DateButton(
                      label: 'Desde',
                      value: tmpSince,
                      onPick: (d) => setSt(() => tmpSince = d),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _DateButton(
                      label: 'Hasta',
                      value: tmpUntil,
                      onPick: (d) => setSt(() => tmpUntil = d),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        setSt(() {
                          tmpSince = tmpUntil = tmpChannel = null;
                        });
                      },
                      child: const Text('Limpiar'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: () {
                        setState(() {
                          _since = tmpSince;
                          _until = tmpUntil;
                          _channel = tmpChannel;
                        });
                        Navigator.pop(sheetCtx);
                        ctx.read<LitersByStyleBloc>().add(
                            LitersByStyleLoadRequested(
                                since: _since,
                                until: _until,
                                channel: _channel));
                      },
                      child: const Text('Aplicar'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Analytics Body ───────────────────────────────────────────────────────────

class _AnalyticsBody extends StatelessWidget {
  const _AnalyticsBody({
    required this.summary,
    required this.colorFor,
    this.since,
    this.until,
    this.channel,
  });

  final StyleLitersSummary summary;
  final Color Function(int) colorFor;
  final String? since;
  final String? until;
  final String? channel;

  @override
  Widget build(BuildContext context) {
    final currency = NumberFormat.currency(symbol: '\$', decimalDigits: 0);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── KPI Row ──────────────────────────────────────────────────────
        Row(
          children: [
            _Kpi(
              '${summary.totalLiters.toStringAsFixed(1)} L',
              'Total Litros',
              DesertBrewColors.primary,
            ),
            const SizedBox(width: 12),
            _Kpi(
              '${summary.styles.length}',
              'Estilos',
              DesertBrewColors.accent,
            ),
            const SizedBox(width: 12),
            _Kpi(
              currency.format(
                  summary.styles.fold(0.0, (s, e) => s + e.revenue)),
              'Revenue',
              DesertBrewColors.success,
            ),
          ],
        ),
        if (since != null || until != null || channel != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              [
                if (channel != null) 'Canal: $channel',
                if (since != null) 'Desde: $since',
                if (until != null) 'Hasta: $until',
              ].join(' · '),
              style: const TextStyle(
                  color: DesertBrewColors.textHint, fontSize: 11),
            ),
          ),
        const SizedBox(height: 20),

        // ── Horizontal bar chart ─────────────────────────────────────────
        const Text('Distribución por Estilo',
            style: TextStyle(
                fontWeight: FontWeight.bold,
                color: DesertBrewColors.textSecondary,
                fontSize: 13)),
        const SizedBox(height: 12),

        ...summary.styles.asMap().entries.map((entry) {
          final i = entry.key;
          final s = entry.value;
          final color = colorFor(i);
          return _StyleBar(
            entry: s,
            color: color,
            totalLiters: summary.totalLiters,
            currency: currency,
          );
        }),
        const SizedBox(height: 24),

        // ── Ranking table ────────────────────────────────────────────────
        const Text('Detalle por Estilo',
            style: TextStyle(
                fontWeight: FontWeight.bold,
                color: DesertBrewColors.textSecondary,
                fontSize: 13)),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: DesertBrewColors.surface,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: summary.styles.asMap().entries.map((entry) {
              final i = entry.key;
              final s = entry.value;
              return ListTile(
                dense: true,
                leading: CircleAvatar(
                  radius: 10,
                  backgroundColor: colorFor(i),
                  child: Text(
                    '${i + 1}',
                    style: const TextStyle(
                        fontSize: 8,
                        color: Colors.white,
                        fontWeight: FontWeight.bold),
                  ),
                ),
                title: Text(s.style,
                    style: const TextStyle(fontSize: 13)),
                subtitle: Text(
                    '${s.noteCount} nota${s.noteCount != 1 ? 's' : ''}',
                    style: const TextStyle(
                        color: DesertBrewColors.textHint, fontSize: 11)),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '${s.totalLiters.toStringAsFixed(1)} L',
                      style: TextStyle(
                          color: colorFor(i),
                          fontWeight: FontWeight.bold,
                          fontSize: 13),
                    ),
                    Text(
                      currency.format(s.revenue),
                      style: const TextStyle(
                          color: DesertBrewColors.textHint, fontSize: 11),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}

// ── Horizontal Bar ───────────────────────────────────────────────────────────

class _StyleBar extends StatelessWidget {
  const _StyleBar({
    required this.entry,
    required this.color,
    required this.totalLiters,
    required this.currency,
  });

  final StyleLitersEntry entry;
  final Color color;
  final double totalLiters;
  final NumberFormat currency;

  @override
  Widget build(BuildContext context) {
    final frac = totalLiters > 0
        ? (entry.totalLiters / totalLiters).clamp(0.0, 1.0)
        : 0.0;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  entry.style,
                  style: const TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w500),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(
                '${entry.totalLiters.toStringAsFixed(1)} L  ${entry.pct.toStringAsFixed(1)}%',
                style: TextStyle(
                    color: color,
                    fontSize: 11,
                    fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Stack(
            children: [
              // Background track
              Container(
                height: 10,
                decoration: BoxDecoration(
                  color: DesertBrewColors.surface,
                  borderRadius: BorderRadius.circular(5),
                ),
              ),
              // Filled bar
              FractionallySizedBox(
                widthFactor: frac,
                child: Container(
                  height: 10,
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(5),
                    boxShadow: [
                      BoxShadow(
                        color: color.withValues(alpha: 0.4),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

class _Kpi extends StatelessWidget {
  const _Kpi(this.value, this.label, this.color);
  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.2)),
        ),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    color: color,
                    fontSize: 15,
                    fontWeight: FontWeight.bold),
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center),
            Text(label,
                style: const TextStyle(
                    color: DesertBrewColors.textHint, fontSize: 10),
                textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class _DateButton extends StatelessWidget {
  const _DateButton({
    required this.label,
    required this.value,
    required this.onPick,
  });
  final String label;
  final String? value;
  final ValueChanged<String?> onPick;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () async {
        final picked = await showDatePicker(
          context: context,
          initialDate: value != null
              ? DateTime.tryParse(value!) ?? DateTime.now()
              : DateTime.now(),
          firstDate: DateTime(2020),
          lastDate: DateTime(2030),
        );
        if (picked != null) {
          onPick(DateFormat('yyyy-MM-dd').format(picked));
        }
      },
      icon: const Icon(Icons.calendar_today_rounded, size: 14),
      label: Text(value ?? label, style: const TextStyle(fontSize: 12)),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty({required this.hasFilters, required this.onClear});
  final bool hasFilters;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.bar_chart_rounded,
              size: 64, color: DesertBrewColors.textHint),
          const SizedBox(height: 12),
          const Text(
            'Sin datos para mostrar',
            style: TextStyle(color: DesertBrewColors.textSecondary),
          ),
          const SizedBox(height: 4),
          const Text(
            'Confirma notas de venta para ver el análisis',
            style: TextStyle(
                color: DesertBrewColors.textHint, fontSize: 12),
            textAlign: TextAlign.center,
          ),
          if (hasFilters) ...[
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: onClear,
              child: const Text('Limpiar filtros'),
            ),
          ],
        ],
      ),
    );
  }
}

class _Error extends StatelessWidget {
  const _Error({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.wifi_off_rounded,
              size: 48, color: DesertBrewColors.error),
          const SizedBox(height: 12),
          Text(message,
              style: const TextStyle(
                  color: DesertBrewColors.textHint, fontSize: 12)),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}
