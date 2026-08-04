import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class MonPackScreen extends StatefulWidget {
  const MonPackScreen({super.key});

  @override
  State<MonPackScreen> createState() => _MonPackScreenState();
}

class _MonPackScreenState extends State<MonPackScreen> {
  Map<String, dynamic>? _monPack;
  List<dynamic> _availablePacks = [];
  List<dynamic> _scheduledChanges = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() { _loading = true; _error = null; });
    try {
      final api = ApiService();
      final token = await SecureStorage.getToken();
      api.setToken(token);
      final results = await Future.wait([
        api.getMonPack(),
        api.getPackDefinitions(),
        api.getScheduledChanges(),
      ]);
      setState(() {
        _monPack = results[0] as Map<String, dynamic>;
        _availablePacks = results[1] as List<dynamic>;
        _scheduledChanges = results[2] as List<dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _subscribeToPack(int packId) async {
    try {
      final api = ApiService();
      final token = await SecureStorage.getToken();
      api.setToken(token);
      await api.subscribeToPack(packId);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pack souscrit avec succès!'), backgroundColor: Colors.green),
      );
      _loadData();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
      );
    }
  }

  Color _tierColor(String tier) {
    switch (tier) {
      case 'gratuit': return Colors.grey;
      case 'basique': return Colors.blue;
      case 'silver': return Colors.grey.shade600;
      case 'golden': return const Color(0xFFFFB300);
      default: return Colors.grey;
    }
  }

  IconData _tierIcon(String tier) {
    switch (tier) {
      case 'gratuit': return Icons.free_breakfast;
      case 'basique': return Icons.star_border;
      case 'silver': return Icons.star_half;
      case 'golden': return Icons.star;
      default: return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mon Pack'), backgroundColor: const Color(0xFF0D1B2A), foregroundColor: Colors.white),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Text(_error!), const SizedBox(height: 16), ElevatedButton(onPressed: _loadData, child: const Text('Retry'))]))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (_monPack != null) ...[
                        _buildCurrentPack(),
                        const SizedBox(height: 24),
                      ],
                      if (_scheduledChanges.isNotEmpty) ...[
                        const Text('Changements programmés', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        ..._scheduledChanges.map((sc) => Card(child: ListTile(
                          leading: const Icon(Icons.schedule, color: Colors.orange),
                          title: Text('Downgrade vers ${sc['target_tier']}'),
                          subtitle: Text('Effective: ${sc['effective_date']}'),
                        ))),
                        const SizedBox(height: 24),
                      ],
                      const Text('Packs disponibles', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      ..._availablePacks.map((pack) => _buildPackCard(pack)),
                    ],
                  ),
                ),
    );
  }

  Widget _buildCurrentPack() {
    final tier = _monPack?['current_tier'] ?? 'gratuit';
    final packName = _monPack?['pack_name'] ?? 'Gratuit';
    final niveau = _monPack?['niveau_scolaire'] ?? '';
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [_tierColor(tier), _tierColor(tier).withOpacity(0.7)]),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(_tierIcon(tier), color: Colors.white, size: 32),
            const SizedBox(width: 12),
            Expanded(child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(packName, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                Text(niveau, style: const TextStyle(color: Colors.white70)),
              ],
            )),
          ]),
          const SizedBox(height: 12),
          Text('Tier: ${tier.toUpperCase()}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildPackCard(dynamic pack) {
    final tier = pack['tier'] ?? 'gratuit';
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: Icon(_tierIcon(tier), color: _tierColor(tier), size: 36),
        title: Text(pack['nom'] ?? pack['name'] ?? 'Pack', style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text('${pack['nb_matieres_principales'] ?? 0} matières • ${pack['price_tnd'] ?? 0} TND/trimestre'),
        trailing: ElevatedButton(
          onPressed: () => _subscribeToPack(pack['id']),
          style: ElevatedButton.styleFrom(backgroundColor: _tierColor(tier), foregroundColor: Colors.white),
          child: const Text('Souscrire'),
        ),
      ),
    );
  }
}
