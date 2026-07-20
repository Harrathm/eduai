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
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF4F46E5)),
          useMaterial3: true,
        ),
        routerConfig: appRouter,
      ),
    );
  }
}