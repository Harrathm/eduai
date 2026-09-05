import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../bloc/auth_bloc.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailController = TextEditingController();
  bool _sent = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  void _handleSubmit() {
    if (_emailController.text.trim().isEmpty) return;
    context.read<AuthBloc>().add(AuthForgotPasswordRequested(
          email: _emailController.text.trim(),
        ));
    setState(() => _sent = true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.go('/login')),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: _sent
              ? Column(
                  children: [
                    const SizedBox(height: 80),
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(color: Colors.green.withOpacity(0.1), shape: BoxShape.circle),
                      child: const Icon(Icons.mark_email_read, size: 40, color: Colors.green),
                    ),
                    const SizedBox(height: 24),
                    const Text('Check Your Email', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    Text(
                      'We sent a password reset link to\n${_emailController.text}',
                      style: const TextStyle(fontSize: 15, color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: () => context.go('/login'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF0D1B2A),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text('Back to Sign In'),
                    ),
                  ],
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: 80),
                    Center(
                      child: Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(color: const Color(0xFFFF6B2B).withOpacity(0.1), shape: BoxShape.circle),
                        child: const Icon(Icons.lock_reset, size: 36, color: Color(0xFFFF6B2B)),
                      ),
                    ),
                    const SizedBox(height: 24),
                    const Text('Forgot Password?', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    const Text(
                      'Enter your email and we\'ll send you a link to reset your password.',
                      style: TextStyle(fontSize: 15, color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.email_outlined),
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _handleSubmit,
                      child: const Text('Send Reset Link', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => context.go('/login'),
                      child: const Text('Back to Sign In'),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}
