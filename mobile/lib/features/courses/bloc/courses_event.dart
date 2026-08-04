part of 'courses_bloc.dart';

abstract class CoursesEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class CoursesLoadRequested extends CoursesEvent {}
