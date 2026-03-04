import 'package:equatable/equatable.dart';

class TipPoolParticipant extends Equatable {
  const TipPoolParticipant({
    required this.employeeId,
    required this.name,
    required this.share,
  });

  final int employeeId;
  final String name;
  final double share;

  @override
  List<Object?> get props => [employeeId, name, share];
}

class TipPool extends Equatable {
  const TipPool({
    required this.id,
    required this.weekStart,
    required this.weekEnd,
    required this.totalCollected,
    required this.numParticipants,
    required this.perPersonShare,
    required this.createdAt,
    this.notes,
    this.createdBy,
    this.participants = const [],
  });

  final int id;
  final DateTime weekStart;
  final DateTime weekEnd;
  final double totalCollected;
  final int numParticipants;
  final double perPersonShare;
  final DateTime createdAt;
  final String? notes;
  final String? createdBy;
  final List<TipPoolParticipant> participants;

  @override
  List<Object?> get props => [
    id,
    weekStart,
    weekEnd,
    totalCollected,
    numParticipants,
    perPersonShare,
    createdAt,
    notes,
    createdBy,
    participants,
  ];
}
