import 'package:equatable/equatable.dart';

/// Aggregated liters sold per beer style.
class StyleLitersSummary extends Equatable {
  const StyleLitersSummary({
    required this.styles,
    required this.totalLiters,
    this.since,
    this.until,
    this.channel,
  });

  final List<StyleLitersEntry> styles;
  final double totalLiters;
  final String? since;
  final String? until;
  final String? channel;

  @override
  List<Object?> get props => [totalLiters, styles];
}

class StyleLitersEntry extends Equatable {
  const StyleLitersEntry({
    required this.style,
    required this.totalLiters,
    required this.noteCount,
    required this.revenue,
    required this.pct,
  });

  final String style;
  final double totalLiters;
  final int noteCount;
  final double revenue;
  final double pct;

  @override
  List<Object?> get props => [style, totalLiters];
}
