import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../domain/entities/sales_note.dart';
import '../../../domain/repositories/sales_repository.dart';

part 'sales_note_event.dart';
part 'sales_note_state.dart';

class SalesNoteBloc extends Bloc<SalesNoteEvent, SalesNoteState> {
  SalesNoteBloc(this._repository) : super(SalesNoteInitial()) {
    on<SalesNoteLoadRequested>(_onLoad);
    on<SalesNoteCreateSubmitted>(_onCreate);
    on<SalesNoteUpdateRequested>(_onUpdate);
    on<SalesNoteConfirmRequested>(_onConfirm);
    on<SalesNoteMarkPaidRequested>(_onMarkPaid);
    on<SalesNoteCancelRequested>(_onCancel);
    on<SalesNoteDeleteRequested>(_onDelete);
  }

  final SalesRepository _repository;
  List<SalesNote> _notes = [];

  Future<void> _onLoad(
    SalesNoteLoadRequested event,
    Emitter<SalesNoteState> emit,
  ) async {
    emit(SalesNoteLoading());
    try {
      _notes = await _repository.getSalesNotes(
        status: event.status,
        paymentStatus: event.paymentStatus,
        clientId: event.clientId,
      );
      emit(
        SalesNoteLoaded(
          _notes,
          filterStatus: event.status,
          filterPayment: event.paymentStatus,
        ),
      );
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }

  Future<void> _onCreate(
    SalesNoteCreateSubmitted event,
    Emitter<SalesNoteState> emit,
  ) async {
    emit(SalesNoteSubmitting(_notes));
    try {
      final note = await _repository.createSalesNote(
        items: event.items,
        clientId: event.clientId,
        clientName: event.clientName,
        channel: event.channel,
        paymentMethod: event.paymentMethod,
        includeTaxes: event.includeTaxes,
        includeIeps: event.includeIeps,
        includeIva: event.includeIva,
        notes: event.notes,
        createdBy: event.createdBy,
      );
      emit(SalesNoteCreateSuccess(note));
      add(SalesNoteLoadRequested());
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }

  Future<void> _onConfirm(
    SalesNoteConfirmRequested event,
    Emitter<SalesNoteState> emit,
  ) async {
    try {
      final note = await _repository.confirmSalesNote(event.noteId);
      emit(SalesNoteActionSuccess(note, 'Nota confirmada'));
      add(SalesNoteLoadRequested());
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }

  Future<void> _onMarkPaid(
    SalesNoteMarkPaidRequested event,
    Emitter<SalesNoteState> emit,
  ) async {
    try {
      final note = await _repository.markAsPaid(event.noteId);
      emit(SalesNoteActionSuccess(note, 'Nota marcada como pagada'));
      add(SalesNoteLoadRequested());
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }

  Future<void> _onCancel(
    SalesNoteCancelRequested event,
    Emitter<SalesNoteState> emit,
  ) async {
    try {
      await _repository.cancelSalesNote(event.noteId);
      emit(SalesNoteActionSuccess(null, 'Nota cancelada'));
      add(SalesNoteLoadRequested());
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }

  Future<void> _onUpdate(
    SalesNoteUpdateRequested event,
    Emitter<SalesNoteState> emit,
  ) async {
    try {
      final note = await _repository.updateSalesNote(
        event.noteId,
        event.fields,
      );
      emit(SalesNoteActionSuccess(note, 'Nota actualizada'));
      add(SalesNoteLoadRequested());
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }

  Future<void> _onDelete(
    SalesNoteDeleteRequested event,
    Emitter<SalesNoteState> emit,
  ) async {
    try {
      await _repository.deleteSalesNote(event.noteId);
      emit(SalesNoteActionSuccess(null, 'Nota eliminada'));
      add(SalesNoteLoadRequested());
    } catch (e) {
      emit(SalesNoteError(e.toString()));
    }
  }
}
