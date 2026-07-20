import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator localhost
  String? _token;

  final http.Client _client = http.Client();

  void setToken(String? token) {
    _token = token;
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_token != null) 'Authorization': 'Bearer $_token',
  };

  Future<dynamic> get(String path) async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl$path'),
        headers: _headers,
      );
      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl$path'),
        headers: _headers,
        body: body != null ? jsonEncode(body) : null,
      );
      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  Future<dynamic> postForm(String path, {Map<String, dynamic>? body}) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl$path'),
        headers: {
          if (_token != null) 'Authorization': 'Bearer $_token',
        },
        body: body,
      );
      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode == 200 || response.statusCode == 201) {
      if (response.body.isEmpty) return null;
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      throw UnauthorizedException('Unauthorized');
    } else {
      final body = jsonDecode(response.body);
      throw ApiException(body['detail'] ?? 'Unknown error');
    }
  }

  // Auth methods
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await postForm('/auth/login', body: {
      'username': email,
      'password': password,
    });
    if (response['access_token'] != null) {
      _token = response['access_token'];
    }
    return response;
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    return await get('/auth/me');
  }

  Future<List<dynamic>> getCourses() async {
    final response = await get('/api/academy/courses');
    return List<dynamic>.from(response);
  }

  Future<List<dynamic>> getAssignments() async {
    final response = await get('/api/lms/assignments');
    return List<dynamic>.from(response);
  }

  Future<Map<String, dynamic>> submitAssignment(int assignmentId, String content) async {
    return await post('/api/lms/assignments/$assignmentId/submit', body: {
      'content': content,
    });
  }

  Future<Map<String, dynamic>> askAI(String question) async {
    return await post('/api/ai/ask', body: {
      'question': question,
      'mode': 'tutor',
    });
  }

  Future<List<dynamic>> getModulesForCourse(int courseId) async {
    final response = await get('/api/academy/courses/$courseId/modules');
    return List<dynamic>.from(response);
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class UnauthorizedException extends ApiException {
  UnauthorizedException(super.message);
}