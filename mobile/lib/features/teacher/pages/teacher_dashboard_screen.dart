import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class TeacherDashboardScreen extends StatefulWidget {
  const TeacherDashboardScreen({super.key});

  @override
  State<TeacherDashboardScreen> createState() => _TeacherDashboardScreenState();
}

class _TeacherDashboardScreenState extends State<TeacherDashboardScreen> {
  Map<String, dynamic>? _dashboard;
  List<dynamic> _students = [];
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
      final results = await Future.wait([api.getTeacherDashboard(), api.getTeacherStudents()]);
      setState(() {
        _dashboard = results[0] as Map<String, dynamic>;
        _students = results[1] as List<dynamic>;
        _loading = false;
      });
    } catch (e) {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Espace Enseignant'), backgroundColor: const Color(0xFF0D1B2A), foregroundColor: Colors.white),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildStatsRow(),
                  const SizedBox(height: 24),
                  const Text('Mes Élèves', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  ..._students.map((s) => _buildStudentTile(s)),
                  if (_students.isEmpty) const Center(child: Text('Aucun élève')),
                ],
              ),
            ),
    );
  }

  Widget _buildStatsRow() {
    final totalStudents = _dashboard?['total_students'] ?? _students.length;
    final totalCourses = _dashboard?['total_courses'] ?? 0;
    return Row(
      children: [
        _statCard(Icons.people, 'Élèves', '$totalStudents', Colors.blue),
        const SizedBox(width: 12),
        _statCard(Icons.school, 'Cours', '$totalCourses', Colors.green),
        const SizedBox(width: 12),
        _statCard(Icons.trending_up, 'Actifs', '${_dashboard?['active_students'] ?? 0}', Colors.orange),
      ],
    );
  }

  Widget _statCard(IconData icon, String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
        child: Column(children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
          Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
        ]),
      ),
    );
  }

  Widget _buildStudentTile(dynamic student) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: const Color(0xFF0D1B2A).withOpacity(0.1),
          child: Text((student['full_name'] ?? student['email'] ?? '?')[0].toUpperCase()),
        ),
        title: Text(student['full_name'] ?? student['email'] ?? 'Student'),
        subtitle: Text(student['niveau_scolaire'] ?? student['email'] ?? ''),
        trailing: Text('${student['progress_pct'] ?? 0}%', style: const TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
  }
}
