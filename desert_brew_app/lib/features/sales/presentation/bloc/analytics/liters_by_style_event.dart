part of 'liters_by_style_bloc.dart';
abstract class LitersByStyleEvent {}
class LitersByStyleLoadRequested extends LitersByStyleEvent {
  LitersByStyleLoadRequested({this.since, this.until, this.channel});
  final String? since;
  final String? until;
  final String? channel;
}
