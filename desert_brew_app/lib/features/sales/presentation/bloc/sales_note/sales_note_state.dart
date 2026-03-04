part of 'sales_note_bloc.dart';
abstract class SalesNoteState {}
class SalesNoteInitial extends SalesNoteState {}
class SalesNoteLoading extends SalesNoteState {}
class SalesNoteSubmitting extends SalesNoteState {
  SalesNoteSubmitting(this.existing);
  final List<SalesNote> existing;
}
class SalesNoteLoaded extends SalesNoteState {
  SalesNoteLoaded(this.notes, {this.filterStatus, this.filterPayment});
  final List<SalesNote> notes;
  final String? filterStatus;
  final String? filterPayment;
}
class SalesNoteCreateSuccess extends SalesNoteState {
  SalesNoteCreateSuccess(this.note);
  final SalesNote note;
}
class SalesNoteActionSuccess extends SalesNoteState {
  SalesNoteActionSuccess(this.note, this.message);
  final SalesNote? note;
  final String message;
}
class SalesNoteError extends SalesNoteState {
  SalesNoteError(this.message);
  final String message;
}
