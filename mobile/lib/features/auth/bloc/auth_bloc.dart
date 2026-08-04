import 'dart:convert';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

// Events
abstract class AuthEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthCheckRequested extends AuthEvent {}

class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;
  AuthLoginRequested({required this.email, required this.password});
  @override
  List<Object?> get props => [email, password];
}

class AuthRegisterRequested extends AuthEvent {
  final String fullName;
  final String email;
  final String password;
  AuthRegisterRequested({required this.fullName, required this.email, required this.password});
  @override
  List<Object?> get props => [fullName, email, password];
}

class AuthForgotPasswordRequested extends AuthEvent {
  final String email;
  AuthForgotPasswordRequested({required this.email});
  @override
  List<Object?> get props => [email];
}

class AuthResetPasswordRequested extends AuthEvent {
  final String token;
  final String newPassword;
  AuthResetPasswordRequested({required this.token, required this.newPassword});
  @override
  List<Object?> get props => [token, newPassword];
}

class AuthLogoutRequested extends AuthEvent {}

// States
abstract class AuthState extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}

class AuthAuthenticated extends AuthState {
  final Map<String, dynamic> user;
  AuthAuthenticated({required this.user});
  @override
  List<Object?> get props => [user];
}

class AuthUnauthenticated extends AuthState {}

class AuthPasswordResetSent extends AuthState {}

class AuthPasswordResetDone extends AuthState {}

class AuthError extends AuthState {
  final String message;
  AuthError({required this.message});
  @override
  List<Object?> get props => [message];
}

// BLoC
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final ApiService _apiService = ApiService();

  AuthBloc() : super(AuthInitial()) {
    on<AuthCheckRequested>(_onAuthCheckRequested);
    on<AuthLoginRequested>(_onAuthLoginRequested);
    on<AuthRegisterRequested>(_onAuthRegisterRequested);
    on<AuthForgotPasswordRequested>(_onAuthForgotPasswordRequested);
    on<AuthResetPasswordRequested>(_onAuthResetPasswordRequested);
    on<AuthLogoutRequested>(_onAuthLogoutRequested);
  }

  Future<void> _onAuthCheckRequested(AuthCheckRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final token = await SecureStorage.getToken();
      if (token != null) {
        _apiService.setToken(token);
        final userData = await SecureStorage.getUser();
        if (userData != null) {
          final user = jsonDecode(userData) as Map<String, dynamic>;
          emit(AuthAuthenticated(user: user));
        } else {
          emit(AuthUnauthenticated());
        }
      } else {
        emit(AuthUnauthenticated());
      }
    } catch (e) {
      emit(AuthUnauthenticated());
    }
  }

  Future<void> _onAuthLoginRequested(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final response = await _apiService.login(event.email, event.password);
      if (response['access_token'] != null) {
        final token = response['access_token'];
        await SecureStorage.saveToken(token);
        _apiService.setToken(token);

        final refreshToken = response['refresh_token'];
        if (refreshToken != null) {
          await SecureStorage.saveRefreshToken(refreshToken);
        }

        final user = await _apiService.getCurrentUser();
        await SecureStorage.saveUser(jsonEncode(user));
        emit(AuthAuthenticated(user: user));
      } else {
        emit(AuthError(message: response['detail'] ?? 'Login failed'));
      }
    } catch (e) {
      emit(AuthError(message: e.toString()));
    }
  }

  Future<void> _onAuthRegisterRequested(AuthRegisterRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      final response = await _apiService.register(event.fullName, event.email, event.password);
      if (response['access_token'] != null) {
        final token = response['access_token'];
        await SecureStorage.saveToken(token);
        _apiService.setToken(token);

        final refreshToken = response['refresh_token'];
        if (refreshToken != null) {
          await SecureStorage.saveRefreshToken(refreshToken);
        }

        final user = await _apiService.getCurrentUser();
        await SecureStorage.saveUser(jsonEncode(user));
        emit(AuthAuthenticated(user: user));
      } else {
        emit(AuthError(message: response['detail'] ?? 'Registration failed'));
      }
    } catch (e) {
      emit(AuthError(message: e.toString()));
    }
  }

  Future<void> _onAuthForgotPasswordRequested(AuthForgotPasswordRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _apiService.forgotPassword(event.email);
      emit(AuthPasswordResetSent());
    } catch (e) {
      emit(AuthError(message: e.toString()));
    }
  }

  Future<void> _onAuthResetPasswordRequested(AuthResetPasswordRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _apiService.resetPassword(event.token, event.newPassword);
      emit(AuthPasswordResetDone());
    } catch (e) {
      emit(AuthError(message: e.toString()));
    }
  }

  Future<void> _onAuthLogoutRequested(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    await SecureStorage.clearAll();
    _apiService.setToken(null);
    emit(AuthUnauthenticated());
  }
}
