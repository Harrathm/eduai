export abstract class CoursesEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

export class CoursesLoadRequested extends CoursesEvent {}
export class CourseSelected extends CoursesEvent {
  final Map<String, dynamic> course;
  CourseSelected({required this.course});
  @override
  List<Object?> get props => [course];
}