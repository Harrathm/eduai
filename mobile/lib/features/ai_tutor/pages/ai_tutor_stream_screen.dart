import 'package:flutter/material.dart';
import '../../../core/api/api_service.dart';
import '../../../core/storage/secure_storage.dart';

class Message {
  final String content;
  final bool isUser;
  final DateTime timestamp;
  Message({required this.content, required this.isUser, required this.timestamp});
}

class AITutorStreamScreen extends StatefulWidget {
  const AITutorStreamScreen({super.key});

  @override
  State<AITutorStreamScreen> createState() => _AITutorStreamScreenState();
}

class _AITutorStreamScreenState extends State<AITutorStreamScreen> {
  final List<Message> _messages = [
    Message(
      content: "Bonjour! Je suis votre tuteur IA. Posez-moi vos questions sur vos cours!",
      isUser: false,
      timestamp: DateTime.now(),
    ),
  ];
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _loading = false;
  String _streamBuffer = '';

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(_scrollController.position.maxScrollExtent, duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _sendMessage() async {
    if (_controller.text.trim().isEmpty || _loading) return;
    final question = _controller.text.trim();
    _controller.clear();

    setState(() {
      _messages.add(Message(content: question, isUser: true, timestamp: DateTime.now()));
      _loading = true;
      _streamBuffer = '';
      _messages.add(Message(content: '', isUser: false, timestamp: DateTime.now()));
    });
    _scrollToBottom();

    try {
      final api = ApiService();
      final token = await SecureStorage.getToken();
      api.setToken(token);

      await for (final chunk in api.askAIStream(question)) {
        setState(() {
          _streamBuffer += chunk;
          _messages.last = Message(content: _streamBuffer, isUser: false, timestamp: DateTime.now());
        });
        _scrollToBottom();
      }
    } catch (e) {
      setState(() {
        _messages.last = Message(content: 'Désolé, une erreur est survenue. Réessayez.', isUser: false, timestamp: DateTime.now());
      });
    } finally {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tuteur IA'),
        backgroundColor: const Color(0xFF0D1B2A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {},
            tooltip: 'Historique',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _buildMessageBubble(msg);
              },
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(children: [
                SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                SizedBox(width: 8),
                Text('En train de réfléchir...', style: TextStyle(fontSize: 12, color: Colors.grey)),
              ]),
            ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.white, boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)]),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                      decoration: InputDecoration(
                        hintText: 'Posez une question...',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: const Color(0xFF0D1B2A),
                    child: IconButton(
                      icon: const Icon(Icons.send, color: Colors.white, size: 20),
                      onPressed: _loading ? null : _sendMessage,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(Message msg) {
    final isUser = msg.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF0D1B2A) : Colors.grey.shade100,
          borderRadius: BorderRadius.circular(16).copyWith(bottomRight: isUser ? const Radius.circular(4) : null, bottomLeft: !isUser ? const Radius.circular(4) : null),
        ),
        child: Text(
          msg.content.isEmpty ? '...' : msg.content,
          style: TextStyle(color: isUser ? Colors.white : Colors.black87, fontSize: 15),
        ),
      ),
    );
  }
}
