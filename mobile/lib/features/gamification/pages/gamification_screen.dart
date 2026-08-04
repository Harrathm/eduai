import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class GamificationScreen extends StatefulWidget {
  const GamificationScreen({super.key});

  @override
  State<GamificationScreen> createState() => _GamificationScreenState();
}

class _GamificationScreenState extends State<GamificationScreen> {
  List<dynamic> _badges = [];
  Map<String, dynamic>? _streak;
  List<dynamic> _rankings = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() { _loading = true; });
    try {
      final api = ApiService();
      final token = await SecureStorage.getToken();
      api.setToken(token);
      final results = await Future.wait([api.getBadges(), api.getStreak(), api.getRankings()]);
      setState(() {
        _badges = results[0] as List<dynamic>;
        _streak = results[1] as Map<String, dynamic>;
        _rankings = results[2] as List<dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gamification'), backgroundColor: const Color(0xFF0D1B2A), foregroundColor: Colors.white),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildStreakCard(),
                  const SizedBox(height: 24),
                  const Text('Badges', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: _badges.map((b) => _buildBadge(b)).toList(),
                  ),
                  if (_badges.isEmpty) const Center(child: Text('Pas encore de badges')),
                  const SizedBox(height: 24),
                  const Text('Classement', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  ..._rankings.asMap().entries.map((entry) => _buildRankingTile(entry.key, entry.value)),
                ],
              ),
            ),
    );
  }

  Widget _buildStreakCard() {
    final current = _streak?['current_streak'] ?? 0;
    final longest = _streak?['longest_streak'] ?? 0;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFFFF6B2B), Color(0xFFFF8C42)]),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Column(children: [
            const Icon(Icons.local_fire_department, color: Colors.white, size: 36),
            const SizedBox(height: 4),
            Text('$current', style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
            const Text('Série actuelle', style: TextStyle(color: Colors.white70)),
          ]),
          Column(children: [
            const Icon(Icons.emoji_events, color: Colors.white, size: 36),
            const SizedBox(height: 4),
            Text('$longest', style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
            const Text('Meilleure série', style: TextStyle(color: Colors.white70)),
          ]),
        ],
      ),
    );
  }

  Widget _buildBadge(dynamic badge) {
    final earned = badge['earned'] == true;
    return Container(
      width: 80,
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: earned ? Colors.amber.withOpacity(0.15) : Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: earned ? Colors.amber : Colors.grey.shade300),
      ),
      child: Column(children: [
        Icon(Icons.emoji_events, size: 32, color: earned ? Colors.amber : Colors.grey),
        const SizedBox(height: 4),
        Text(badge['name'] ?? '', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: earned ? Colors.black87 : Colors.grey), textAlign: TextAlign.center),
      ]),
    );
  }

  Widget _buildRankingTile(int index, dynamic entry) {
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: index == 0 ? Colors.amber : index == 1 ? Colors.grey.shade400 : index == 2 ? Colors.brown : Colors.grey.shade200,
        child: Text('${index + 1}', style: const TextStyle(fontWeight: FontWeight.bold)),
      ),
      title: Text(entry['full_name'] ?? entry['email'] ?? 'Student'),
      trailing: Text('${entry['xp'] ?? entry['points'] ?? 0} XP', style: const TextStyle(fontWeight: FontWeight.bold)),
    );
  }
}
