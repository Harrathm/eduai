import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../bloc/auth_bloc.dart';

class ResetPasswordScreen extends StatefulWidget {
  final String token;
  const ResetPasswordScreen({super.key, required this.token});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscure = true;
  bool _reset = false;

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  void _handleReset() {
    if (_passwordController.text != _confirmController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passwords do not match'), backgroundColor: Colors.red),
      );
      return;
    }
    if (_passwordController.text.length < 8) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password must be at least 8 characters'), backgroundColor: Colors.red),
      );
      return;
    }
    context.read<AuthBloc>().add(AuthResetPasswordRequested(
          token: widget.token,
          newPassword: _passwordController.text,
        ));
    setState(() => _reset = true);
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
          child: _reset
              ? Column(
                  children: [
                    const SizedBox(height: 80),
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(color: Colors.green.withOpacity(0.1), shape: BoxShape.circle),
                      child: const Icon(Icons.check_circle, size: 40, color: Colors.green),
                    ),
                    const SizedBox(height: 24),
                    const Text('Password Reset!', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    const Text('Your password has been reset successfully.', style: TextStyle(fontSize: 15, color: Colors.grey), textAlign: TextAlign.center),
                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: () => context.go('/login'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF0D1B2A),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text('Sign In'),
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
                        decoration: BoxDecoration(color: const Color(0xFF0D1B2A).withOpacity(0.1), shape: BoxShape.circle),
                        child: const Icon(Icons.lock_reset, size: 36, color: Color(0xFF0D1B2A)),
                      ),
                    ),
                    const SizedBox(height: 24),
                    const Text('Reset Password', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    const Text('Enter your new password below.', style: TextStyle(fontSize: 15, color: Colors.grey), textAlign: TextAlign.center),
                    const SizedBox(height: 32),
                    TextField(
                      controller: _passwordController,
                      obscureText: _obscure,
                      decoration: InputDecoration(
                        labelText: 'New Password',
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                          onPressed: () => setState(() => _obscure = !_obscure),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _confirmController,
                      obscureText: true,
                      decoration: InputDecoration(
                        labelText: 'Confirm Password',
                        prefixIcon: Icon(Icons.lock_outline),
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _handleReset,
                      child: const Text('Reset Password', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}
