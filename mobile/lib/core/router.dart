import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../features/splash/splash_screen.dart';
import '../features/auth/pages/login_screen.dart';
import '../features/auth/pages/register_screen.dart';
import '../features/auth/pages/forgot_password_screen.dart';
import '../features/auth/pages/reset_password_screen.dart';
import '../features/auth/bloc/auth_bloc.dart';
import '../features/home/pages/home_screen.dart';
import '../features/pack/pages/mon_pack_screen.dart';
import '../features/wallet/pages/wallet_screen.dart';
import '../features/gamification/pages/gamification_screen.dart';
import '../features/catalog/pages/catalog_screen.dart';
import '../features/parent/pages/parent_dashboard_screen.dart';
import '../features/teacher/pages/teacher_dashboard_screen.dart';
import '../features/ai_tutor/pages/ai_tutor_stream_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  redirect: (context, state) {
    final authState = context.read<AuthBloc>().state;
    final isOnAuth = state.matchedLocation == '/login' ||
        state.matchedLocation == '/register' ||
        state.matchedLocation.startsWith('/forgot-password') ||
        state.matchedLocation.startsWith('/reset-password');

    if (authState is AuthAuthenticated && isOnAuth) {
      return '/home';
    }
    if (authState is! AuthAuthenticated && !isOnAuth && state.matchedLocation != '/') {
      return '/login';
    }
    return null;
  },
  routes: [
    GoRoute(path: '/', name: 'splash', builder: (_, __) => const SplashScreen()),
    GoRoute(path: '/login', name: 'login', builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/register', name: 'register', builder: (_, __) => const RegisterScreen()),
    GoRoute(path: '/forgot-password', name: 'forgotPassword', builder: (_, __) => const ForgotPasswordScreen()),
    GoRoute(
      path: '/reset-password',
      name: 'resetPassword',
      builder: (context, state) {
        final token = state.uri.queryParameters['token'] ?? '';
        return ResetPasswordScreen(token: token);
      },
    ),
    GoRoute(path: '/home', name: 'home', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/mon-pack', name: 'monPack', builder: (_, __) => const MonPackScreen()),
    GoRoute(path: '/wallet', name: 'wallet', builder: (_, __) => const WalletScreen()),
    GoRoute(path: '/gamification', name: 'gamification', builder: (_, __) => const GamificationScreen()),
    GoRoute(path: '/catalog', name: 'catalog', builder: (_, __) => const CatalogScreen()),
    GoRoute(path: '/ai-tutor', name: 'aiTutorStream', builder: (_, __) => const AITutorStreamScreen()),
    GoRoute(path: '/parent', name: 'parentDashboard', builder: (_, __) => const ParentDashboardScreen()),
    GoRoute(path: '/teacher', name: 'teacherDashboard', builder: (_, __) => const TeacherDashboardScreen()),
  ],
);
