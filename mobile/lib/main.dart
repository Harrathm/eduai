import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'core/router.dart';
import 'features/auth/bloc/auth_bloc.dart';
import 'core/storage/secure_storage.dart';
import 'core/api/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final token = await SecureStorage.getToken();
  if (token != null) {
    ApiService().setToken(token);
  }
  
  runApp(const EDUAIMobileApp());
}

class EDUAIMobileApp extends StatelessWidget {
  const EDUAIMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => AuthBloc()..add(AuthCheckRequested()),
      child: MaterialApp.router(
        title: 'EDUAI Learning',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFFFF6B35),
            primary: const Color(0xFFFF6B35),
            secondary: const Color(0xFF1E3A8A),
            surface: Colors.white,
          ),
          scaffoldBackgroundColor: const Color(0xFFF9FAFB),
          appBarTheme: const AppBarTheme(
            backgroundColor: Colors.white,
            foregroundColor: Color(0xFF1E3A8A),
            elevation: 1,
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            focusedBorder: const OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: Color(0xFFFF6B35), width: 2),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          ),
          cardTheme: CardThemeData(
            color: Colors.white,
            elevation: 2,
            shadowColor: Colors.black.withOpacity(0.08),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF6B35),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          textButtonTheme: TextButtonThemeData(
            style: TextButton.styleFrom(foregroundColor: const Color(0xFF1E3A8A)),
          ),
          useMaterial3: true,
        ),
        routerConfig: appRouter,
      ),
    );
  }
}