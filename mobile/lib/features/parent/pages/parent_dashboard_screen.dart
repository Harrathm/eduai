import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class ParentDashboardScreen extends StatefulWidget {
  const ParentDashboardScreen({super.key});

  @override
  State<ParentDashboardScreen> createState() => _ParentDashboardScreenState();
}

class _ParentDashboardScreenState extends State<ParentDashboardScreen> {
  List<dynamic> _children = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadChildren();
  }

  Future<void> _loadChildren() async {
    setState(() { _loading = true; });
    try {
      final api = ApiService();
      final token = await SecureStorage.getToken();
      api.setToken(token);
      final children = await api.getParentChildren();
      setState(() { _children = children; _loading = false; });
    } catch (e) {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Espace Parent'), backgroundColor: const Color(0xFF0D1B2A), foregroundColor: Colors.white),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadChildren,
              child: _children.isEmpty
                  ? const Center(child: Text('Aucun enfant lié à votre compte'))
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _children.length,
                      itemBuilder: (context, index) => _buildChildCard(_children[index]),
                    ),
            ),
    );
  }

  Widget _buildChildCard(dynamic child) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              CircleAvatar(
                radius: 28,
                backgroundColor: const Color(0xFF0D1B2A).withOpacity(0.1),
                child: Text(
                  (child['full_name'] ?? child['email'] ?? '?')[0].toUpperCase(),
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF0D1B2A)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(child['full_name'] ?? child['email'] ?? 'Enfant', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text(child['niveau_scolaire'] ?? '', style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                ],
              )),
            ]),
            const Divider(height: 24),
            _statRow(Icons.school, 'Pack', child['pack_tier'] ?? 'Gratuit'),
            const SizedBox(height: 8),
            _statRow(Icons.star, 'Palier', child['palier'] ?? 'Découverte'),
            const SizedBox(height: 8),
            _statRow(Icons.trending_up, 'Progression', '${child['progress_pct'] ?? 0}%'),
          ],
        ),
      ),
    );
  }

  Widget _statRow(IconData icon, String label, String value) {
    return Row(children: [
      Icon(icon, size: 18, color: Colors.grey[600]),
      const SizedBox(width: 8),
      Text(label, style: TextStyle(color: Colors.grey[600])),
      const Spacer(),
      Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
    ]);
  }
}
