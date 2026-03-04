import '../../domain/entities/style_liters_summary.dart';

class StyleLitersSummaryModel extends StyleLitersSummary {
  const StyleLitersSummaryModel({
    required super.styles,
    required super.totalLiters,
    super.since,
    super.until,
    super.channel,
  });

  factory StyleLitersSummaryModel.fromJson(Map<String, dynamic> json) {
    final entries = (json['styles'] as List<dynamic>? ?? [])
        .map((e) => StyleLitersEntryModel.fromJson(e as Map<String, dynamic>))
        .toList();
    return StyleLitersSummaryModel(
      styles: entries,
      totalLiters: (json['total_liters'] as num?)?.toDouble() ?? 0,
      since: json['since'] as String?,
      until: json['until'] as String?,
      channel: json['channel'] as String?,
    );
  }
}

class StyleLitersEntryModel extends StyleLitersEntry {
  const StyleLitersEntryModel({
    required super.style,
    required super.totalLiters,
    required super.noteCount,
    required super.revenue,
    required super.pct,
  });

  factory StyleLitersEntryModel.fromJson(Map<String, dynamic> json) {
    return StyleLitersEntryModel(
      style: json['style'] as String? ?? 'Sin estilo',
      totalLiters: (json['total_liters'] as num?)?.toDouble() ?? 0,
      noteCount: (json['note_count'] as num?)?.toInt() ?? 0,
      revenue: (json['revenue'] as num?)?.toDouble() ?? 0,
      pct: (json['pct'] as num?)?.toDouble() ?? 0,
    );
  }
}
