import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  List<dynamic> _courses = [];
  bool _loading = true;
  String _search = '';
  String? _selectedLevel;

  @override
  void initState() {
    super.initState();
    _loadCourses();
  }

  Future<void> _loadCourses() async {
    setState(() { _loading = true; });
    try {
      final api = ApiService();
      final token = await SecureStorage.getToken();
      api.setToken(token);
      final courses = await api.getCourses();
      setState(() { _courses = courses; _loading = false; });
    } catch (e) {
      setState(() { _loading = false; });
    }
  }

  List<dynamic> get _filteredCourses {
    return _courses.where((c) {
      final matchSearch = _search.isEmpty || (c['title']?.toString().toLowerCase().contains(_search.toLowerCase()) ?? false);
      final matchLevel = _selectedLevel == null || c['level'] == _selectedLevel;
      return matchSearch && matchLevel;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Catalogue'), backgroundColor: const Color(0xFF0D1B2A), foregroundColor: Colors.white),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(children: [
                    TextField(
                      decoration: InputDecoration(
                        hintText: 'Rechercher un cours...',
                        prefixIcon: const Icon(Icons.search),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onChanged: (v) => setState(() => _search = v),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 40,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: [
                          _filterChip(null, 'Tous'),
                          _filterChip('primaire', 'Primaire'),
                          _filterChip('preparatoire', 'Préparatoire'),
                          _filterChip('secondaire', 'Secondaire'),
                        ],
                      ),
                    ),
                  ]),
                ),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: _loadCourses,
                    child: _filteredCourses.isEmpty
                        ? const Center(child: Text('Aucun cours trouvé'))
                        : GridView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 16),
                            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 0.8),
                            itemCount: _filteredCourses.length,
                            itemBuilder: (context, index) => _buildCourseCard(_filteredCourses[index]),
                          ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _filterChip(String? value, String label) {
    final selected = _selectedLevel == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label, style: TextStyle(color: selected ? Colors.white : Colors.black87)),
        selected: selected,
        onSelected: (_) => setState(() => _selectedLevel = value),
        selectedColor: const Color(0xFF0D1B2A),
        checkmarkColor: Colors.white,
      ),
    );
  }

  Widget _buildCourseCard(dynamic course) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF0D1B2A).withOpacity(0.05),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              ),
              child: const Icon(Icons.school_rounded, size: 40, color: Color(0xFF0D1B2A)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(course['title'] ?? 'Untitled', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13), maxLines: 2, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 4),
                Text(course['level'] ?? '', style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                const SizedBox(height: 4),
                Row(children: [
                  if (course['price_dt'] != null && course['price_dt'] > 0)
                    Text('${course['price_dt']} DT', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFFF6B2B), fontSize: 12))
                  else
                    const Text('Gratuit', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green, fontSize: 12)),
                ]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
