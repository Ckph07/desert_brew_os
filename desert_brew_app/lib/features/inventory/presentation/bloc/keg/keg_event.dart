part of 'keg_bloc.dart';
abstract class KegEvent {}

class KegLoadRequested extends KegEvent {
  KegLoadRequested({this.stateFilter});
  final String? stateFilter;
}

class KegTransitionRequested extends KegEvent {
  KegTransitionRequested({
    required this.kegId,
    required this.newState,
    required this.userId,
    this.location,
    this.reason,
  });
  final String kegId;
  final String newState;
  final int userId;
  final String? location;
  final String? reason;
}
