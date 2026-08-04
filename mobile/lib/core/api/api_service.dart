import 'package:http/http.dart' as http;
import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

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
      ).timeout(const Duration(seconds: 30));
      return _handleResponse(response);
    } catch (e) {
      if (e is TimeoutException) throw ApiException('Timeout: serveur indisponible');
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body}) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl$path'),
        headers: _headers,
        body: body != null ? jsonEncode(body) : null,
      ).timeout(const Duration(seconds: 30));
      return _handleResponse(response);
    } catch (e) {
      if (e is TimeoutException) throw ApiException('Timeout: serveur indisponible');
      if (e is ApiException) rethrow;
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
      if (e is ApiException) rethrow;
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
      try {
        final body = jsonDecode(response.body);
        throw ApiException(body['detail'] ?? 'Error ${response.statusCode}');
      } catch (_) {
        throw ApiException('Error ${response.statusCode}');
      }
    }
  }

  // ─── Auth ─────────────────────────────────────────────────────────

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

  Future<Map<String, dynamic>> register(String fullName, String email, String password) async {
    final response = await post('/auth/register', body: {
      'full_name': fullName,
      'email': email,
      'password': password,
    });
    if (response['access_token'] != null) {
      _token = response['access_token'];
    }
    return response;
  }

  Future<void> forgotPassword(String email) async {
    await post('/auth/forgot-password', body: {'email': email});
  }

  Future<void> resetPassword(String token, String newPassword) async {
    await post('/auth/reset-password', body: {
      'token': token,
      'new_password': newPassword,
    });
  }

  Future<Map<String, dynamic>> refreshToken(String refreshToken) async {
    final response = await post('/auth/refresh-token', body: {
      'refresh_token': refreshToken,
    });
    if (response['access_token'] != null) {
      _token = response['access_token'];
    }
    return response;
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    return await get('/auth/me');
  }

  // ─── Courses / Learner ────────────────────────────────────────────

  Future<List<dynamic>> getCourses() async {
    final response = await get('/api/learner/courses');
    return List<dynamic>.from(response);
  }

  Future<List<dynamic>> getMyCourses() async {
    final response = await get('/api/learner/my-courses');
    return List<dynamic>.from(response);
  }

  Future<Map<String, dynamic>> getCourseSyllabus(int courseId) async {
    return await get('/api/learner/courses/$courseId/syllabus');
  }

  Future<void> enrollInCourse(int courseId) async {
    await post('/api/learner/courses/$courseId/enroll');
  }

  Future<Map<String, dynamic>> getLearnerDashboard() async {
    return await get('/api/learner/dashboard');
  }

  // ─── Assignments ──────────────────────────────────────────────────

  Future<List<dynamic>> getAssignments() async {
    final response = await get('/api/lms/assignments');
    return List<dynamic>.from(response);
  }

  Future<Map<String, dynamic>> submitAssignment(int assignmentId, String content) async {
    return await post('/api/lms/assignments/$assignmentId/submit', body: {
      'content': content,
    });
  }

  // ─── AI Tutor ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>> askAI(String question) async {
    return await post('/api/ai/ask', body: {
      'question': question,
      'mode': 'tutor',
    });
  }

  Stream<String> askAIStream(String question) async* {
    final request = http.Request('POST', Uri.parse('$baseUrl/api/ai/ask'));
    request.headers.addAll({
      'Content-Type': 'application/json',
      if (_token != null) 'Authorization': 'Bearer $_token',
    });
    request.body = jsonEncode({'question': question, 'mode': 'tutor'});

    final streamedResponse = await _client.send(request).timeout(const Duration(seconds: 60));
    if (streamedResponse.statusCode != 200) {
      throw ApiException('AI request failed: ${streamedResponse.statusCode}');
    }

    await for (final chunk in streamedResponse.stream.transform(utf8.decoder)) {
      final lines = chunk.split('\n');
      for (final line in lines) {
        if (line.startsWith('data: ')) {
          final data = line.substring(6).trim();
          if (data == '[DONE]') return;
          try {
            final json = jsonDecode(data);
            if (json['content'] != null) {
              yield json['content'] as String;
            }
          } catch (_) {}
        }
      }
    }
  }

  Future<List<dynamic>> getAIHistory() async {
    final response = await get('/api/ai/history');
    return List<dynamic>.from(response);
  }

  // ─── Wallet ───────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getWalletBalance() async {
    return await get('/api/wallet/balance');
  }

  Future<List<dynamic>> getWalletHistory({int skip = 0, int limit = 20}) async {
    final response = await get('/api/wallet/history?skip=$skip&limit=$limit');
    if (response is List) return response;
    return response['items'] ?? [];
  }

  // ─── Packs / Abonnements ──────────────────────────────────────────

  Future<List<dynamic>> getPackDefinitions({String? niveauScolaire}) async {
    final qs = niveauScolaire != null ? '?niveau_scolaire=$niveauScolaire' : '';
    final response = await get('/api/abonnements/packs$qs');
    return List<dynamic>.from(response);
  }

  Future<Map<String, dynamic>> getMonPack() async {
    return await get('/api/abonnements/mon-pack');
  }

  Future<Map<String, dynamic>> subscribeToPack(int packId) async {
    return await post('/api/abonnements', body: {'pack_id': packId});
  }

  Future<Map<String, dynamic>> changeTier(String targetTier) async {
    return await post('/api/abonnements/change-tier', body: {'target_tier': targetTier});
  }

  Future<List<dynamic>> getScheduledChanges() async {
    final response = await get('/api/abonnements/scheduled-changes');
    return List<dynamic>.from(response);
  }

  // ─── Gamification ─────────────────────────────────────────────────

  Future<List<dynamic>> getBadges() async {
    final response = await get('/api/gamification/badges');
    return List<dynamic>.from(response);
  }

  Future<void> checkBadges() async {
    await post('/api/gamification/badges/check');
  }

  Future<Map<String, dynamic>> getStreak() async {
    return await get('/api/gamification/streak');
  }

  Future<void> recordActivity() async {
    await post('/api/gamification/streak/record');
  }

  Future<List<dynamic>> getRankings({int? matiereId}) async {
    final qs = matiereId != null ? '?matiere_id=$matiereId' : '';
    final response = await get('/api/gamification/rankings$qs');
    return List<dynamic>.from(response);
  }

  // ─── Parent ───────────────────────────────────────────────────────

  Future<List<dynamic>> getParentChildren() async {
    final response = await get('/api/users/children');
    return List<dynamic>.from(response);
  }

  Future<Map<String, dynamic>> getChildProgress(int childId) async {
    return await get('/api/learner/dashboard?child_id=$childId');
  }

  // ─── Teacher ──────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getTeacherDashboard() async {
    return await get('/api/learner/dashboard');
  }

  Future<List<dynamic>> getTeacherStudents() async {
    final response = await get('/api/teacher/students');
    return List<dynamic>.from(response);
  }

  // ─── Conversations ────────────────────────────────────────────────

  Future<List<dynamic>> getConversations() async {
    final response = await get('/api/conversations');
    if (response is List) return response;
    return [];
  }

  Future<Map<String, dynamic>> createConversation(String title) async {
    return await post('/api/conversations', body: {'title': title});
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
