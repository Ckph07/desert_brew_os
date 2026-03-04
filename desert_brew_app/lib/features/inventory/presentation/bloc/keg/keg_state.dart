part of 'keg_bloc.dart';
// Named KegBlocState to avoid collision with KegState enum from keg_asset.dart
abstract class KegBlocState {}
class KegInitial extends KegBlocState {}
class KegLoading extends KegBlocState {}
class KegLoaded extends KegBlocState {
  KegLoaded(this.kegs);
  final List<KegAsset> kegs;
}
class KegError extends KegBlocState {
  KegError(this.message);
  final String message;
}
