import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/api/api_service.dart';
import '../../auth/bloc/auth_bloc.dart';

part 'courses_event.dart';
part 'courses_state.dart';

class CoursesBloc extends Bloc<CoursesEvent, CoursesState> {
  final ApiService _apiService = ApiService();

  CoursesBloc() : super(CoursesInitial()) {
    on<CoursesLoadRequested>(_onLoadRequested);
  }

  Future<void> _onLoadRequested(
    CoursesLoadRequested event,
    Emitter<CoursesState> emit,
  ) async {
    emit(CoursesLoading());
    try {
      final courses = await _apiService.getCourses();
      emit(CoursesLoaded(courses: List<Map<String, dynamic>>.from(courses)));
    } catch (e) {
      emit(CoursesError(message: e.toString()));
    }
  }
}