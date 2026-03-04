import '../../domain/entities/tip_pool.dart';

class TipPoolParticipantModel extends TipPoolParticipant {
  const TipPoolParticipantModel({
    required super.employeeId,
    required super.name,
    required super.share,
  });

  factory TipPoolParticipantModel.fromJson(Map<String, dynamic> json) {
    return TipPoolParticipantModel(
      employeeId: (json['employee_id'] as num?)?.toInt() ?? 0,
      name: json['name'] as String? ?? '-',
      share: (json['share'] as num?)?.toDouble() ?? 0,
    );
  }
}

class TipPoolModel extends TipPool {
  const TipPoolModel({
    required super.id,
    required super.weekStart,
    required super.weekEnd,
    required super.totalCollected,
    required super.numParticipants,
    required super.perPersonShare,
    required super.createdAt,
    super.notes,
    super.createdBy,
    super.participants,
  });

  factory TipPoolModel.fromJson(Map<String, dynamic> json) {
    final participants =
        (json['participants'] as List<dynamic>? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(TipPoolParticipantModel.fromJson)
            .toList();

    return TipPoolModel(
      id: json['id'] as int,
      weekStart: DateTime.parse('${json['week_start']}T00:00:00'),
      weekEnd: DateTime.parse('${json['week_end']}T00:00:00'),
      totalCollected: (json['total_collected'] as num?)?.toDouble() ?? 0,
      numParticipants: (json['num_participants'] as num?)?.toInt() ?? 0,
      perPersonShare: (json['per_person_share'] as num?)?.toDouble() ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
      notes: json['notes'] as String?,
      createdBy: json['created_by'] as String?,
      participants: participants,
    );
  }
}
