import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  Map<String, dynamic>? _balance;
  List<dynamic> _history = [];
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
      final results = await Future.wait([api.getWalletBalance(), api.getWalletHistory()]);
      setState(() {
        _balance = results[0] as Map<String, dynamic>;
        _history = results[1] as List<dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mon Wallet'), backgroundColor: const Color(0xFF0D1B2A), foregroundColor: Colors.white),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Text(_error!), const SizedBox(height: 16), ElevatedButton(onPressed: _loadData, child: const Text('Retry'))]))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildBalanceCards(),
                      const SizedBox(height: 24),
                      const Text('Historique', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      ..._history.map((tx) => _buildTransactionTile(tx)),
                      if (_history.isEmpty) const Center(child: Padding(
                        padding: EdgeInsets.all(32),
                        child: Text('Aucune transaction', style: TextStyle(color: Colors.grey)),
                      )),
                    ],
                  ),
                ),
    );
  }

  Widget _buildBalanceCards() {
    final pools = _balance?['pools'] ?? {};
    final totalDT = _balance?['total_dt'] ?? 0;
    final totalTokens = _balance?['total_tokens'] ?? 0;

    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [Color(0xFF0D1B2A), Color(0xFF1A2E4A)]),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Solde total', style: TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 8),
              Row(children: [
                Text('$totalDT DT', style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
                const SizedBox(width: 24),
                Text('$totalTokens Tokens', style: const TextStyle(color: Colors.orange, fontSize: 18, fontWeight: FontWeight.bold)),
              ]),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (pools is Map) ...pools.entries.map((entry) {
          final pool = entry.value;
          return Card(
            child: ListTile(
              leading: Icon(_poolIcon(entry.key), color: _poolColor(entry.key)),
              title: Text(_poolLabel(entry.key)),
              trailing: Text('${pool['balance'] ?? 0} ${pool['type'] ?? 'DT'}', style: TextStyle(fontWeight: FontWeight.bold, color: _poolColor(entry.key))),
              subtitle: pool['expires_at'] != null ? Text('Expire: ${pool['expires_at']}') : null,
            ),
          );
        }),
      ],
    );
  }

  Widget _buildTransactionTile(dynamic tx) {
    final isCredit = (tx['amount'] ?? 0) > 0;
    return ListTile(
      leading: Icon(isCredit ? Icons.add_circle : Icons.remove_circle, color: isCredit ? Colors.green : Colors.red, size: 32),
      title: Text(tx['description'] ?? tx['type'] ?? 'Transaction'),
      subtitle: Text(tx['created_at'] ?? ''),
      trailing: Text('${isCredit ? '+' : ''}${tx['amount'] ?? 0} ${tx['currency'] ?? 'DT'}',
          style: TextStyle(fontWeight: FontWeight.bold, color: isCredit ? Colors.green : Colors.red)),
    );
  }

  Color _poolColor(String pool) {
    switch (pool) {
      case 'subscription': return Colors.blue;
      case 'school_allocated': return Colors.purple;
      case 'trial': return Colors.orange;
      case 'purchased': return Colors.green;
      default: return Colors.grey;
    }
  }

  IconData _poolIcon(String pool) {
    switch (pool) {
      case 'subscription': return Icons.card_membership;
      case 'school_allocated': return Icons.school;
      case 'trial': return Icons.science;
      case 'purchased': return Icons.shopping_cart;
      default: return Icons.account_balance_wallet;
    }
  }

  String _poolLabel(String pool) {
    switch (pool) {
      case 'subscription': return 'Abonnement';
      case 'school_allocated': return 'Alloué par l\'école';
      case 'trial': return 'Essai';
      case 'purchased': return 'Acheté';
      default: return pool;
    }
  }
}
