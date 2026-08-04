part of 'courses_bloc.dart';

abstract class CoursesState extends Equatable {
  @override
  List<Object?> get props => [];
}

class CoursesInitial extends CoursesState {}

class CoursesLoading extends CoursesState {}

class CoursesLoaded extends CoursesState {
  final List<Map<String, dynamic>> courses;

  CoursesLoaded({required this.courses});

  @override
  List<Object?> get props => [courses];
}

class CoursesError extends CoursesState {
  final String message;

  CoursesError({required this.message});

  @override
  List<Object?> get props => [message];
}
