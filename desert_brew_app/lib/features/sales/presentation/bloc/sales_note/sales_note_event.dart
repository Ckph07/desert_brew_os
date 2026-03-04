part of 'sales_note_bloc.dart';

abstract class SalesNoteEvent {}

class SalesNoteLoadRequested extends SalesNoteEvent {
  SalesNoteLoadRequested({this.status, this.paymentStatus, this.clientId});
  final String? status;
  final String? paymentStatus;
  final int? clientId;
}

class SalesNoteCreateSubmitted extends SalesNoteEvent {
  SalesNoteCreateSubmitted({
    required this.items,
    this.clientId,
    this.clientName,
    this.channel = 'B2B',
    this.paymentMethod = 'TRANSFERENCIA',
    this.includeTaxes = false,
    this.notes,
    this.createdBy,
  });
  final List<Map<String, dynamic>> items;
  final int? clientId;
  final String? clientName;
  final String channel;
  final String paymentMethod;
  final bool includeTaxes;
  final String? notes;
  final String? createdBy;
}

class SalesNoteUpdateRequested extends SalesNoteEvent {
  SalesNoteUpdateRequested({required this.noteId, required this.fields});
  final int noteId;
  final Map<String, dynamic> fields;
}

class SalesNoteConfirmRequested extends SalesNoteEvent {
  SalesNoteConfirmRequested(this.noteId);
  final int noteId;
}

class SalesNoteMarkPaidRequested extends SalesNoteEvent {
  SalesNoteMarkPaidRequested(this.noteId);
  final int noteId;
}

class SalesNoteCancelRequested extends SalesNoteEvent {
  SalesNoteCancelRequested(this.noteId);
  final int noteId;
}

class SalesNoteDeleteRequested extends SalesNoteEvent {
  SalesNoteDeleteRequested(this.noteId);
  final int noteId;
}
