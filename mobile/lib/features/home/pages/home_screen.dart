import 'package:flutter/material.dart';
import '../../courses/pages/courses_screen.dart';
import '../../assignments/pages/assignments_screen.dart';
import '../../ai_tutor/pages/ai_tutor_stream_screen.dart';
import '../../gamification/pages/gamification_screen.dart';
import '../../pack/pages/mon_pack_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const _DashboardTab(),
    const CoursesScreen(),
    const AITutorStreamScreen(),
    const AssignmentsScreen(),
    const GamificationScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Accueil'),
          NavigationDestination(icon: Icon(Icons.school_outlined), selectedIcon: Icon(Icons.school), label: 'Cours'),
          NavigationDestination(icon: Icon(Icons.smart_toy_outlined), selectedIcon: Icon(Icons.smart_toy), label: 'IA'),
          NavigationDestination(icon: Icon(Icons.assignment_outlined), selectedIcon: Icon(Icons.assignment), label: 'Tâches'),
          NavigationDestination(icon: Icon(Icons.emoji_events_outlined), selectedIcon: Icon(Icons.emoji_events), label: 'Badges'),
        ],
      ),
    );
  }
}

class _DashboardTab extends StatelessWidget {
  const _DashboardTab();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('EDUAI Learning'),
        backgroundColor: const Color(0xFF0D1B2A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF0D1B2A), Color(0xFF2C4A6E)]),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Bienvenue!', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text('Continuez votre apprentissage', style: TextStyle(color: Colors.white70)),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: const Color(0xFF0D1B2A)),
                    child: const Text('Continuer'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const Text('Accès rapide', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Row(
              children: [
                _quickAction(context, Icons.card_membership, 'Mon Pack', '/mon-pack'),
                const SizedBox(width: 12),
                _quickAction(context, Icons.account_balance_wallet, 'Wallet', '/wallet'),
                const SizedBox(width: 12),
                _quickAction(context, Icons.smart_toy, 'Tuteur IA', '/ai-tutor'),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _quickAction(context, Icons.emoji_events, 'Badges', '/gamification'),
                const SizedBox(width: 12),
                _quickAction(context, Icons.library_books, 'Catalogue', '/catalog'),
                const SizedBox(width: 12),
                _quickAction(context, Icons.people, 'Parent', '/parent'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _quickAction(BuildContext context, IconData icon, String label, String route) {
    return Expanded(
      child: InkWell(
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) {
          const routes = {
            '/mon-pack': MonPackScreen(),
            '/wallet': WalletScreen(),
            '/ai-tutor': AITutorStreamScreen(),
            '/gamification': GamificationScreen(),
            '/catalog': CatalogScreen(),
          };
          return routes[route] ?? const SizedBox();
        })),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade200), borderRadius: BorderRadius.circular(12)),
          child: Column(children: [
            Icon(icon, color: const Color(0xFF0D1B2A)),
            const SizedBox(height: 8),
            Text(label, style: const TextStyle(fontSize: 11), textAlign: TextAlign.center),
          ]),
        ),
      ),
    );
  }
}
