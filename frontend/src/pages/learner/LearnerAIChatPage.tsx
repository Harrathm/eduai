import { useAIChat } from "../../features/learner/hooks/useAIChat";
import { ChatSidebar, ChatMessage, ChatInputBar, TypingIndicator, WelcomeMessage } from "../../features/learner/components/chat";

export default function LearnerAIChatPage() {
  const chat = useAIChat();

  return (
    <div className="flex h-[calc(100vh-64px)] bg-cream-m">
      <ChatSidebar
        conversations={chat.filteredConversations}
        activeConvId={chat.activeConvId}
        searchQuery={chat.searchQuery}
        deleteConfirmId={chat.deleteConfirmId}
        onSearchChange={chat.setSearchQuery}
        onStartNew={chat.startNew}
        onOpenConversation={chat.openConversation}
        onDeleteConfirmToggle={(id) =>
          chat.setDeleteConfirmId(chat.deleteConfirmId === id ? null : id)
        }
        onDelete={chat.handleDeleteConversation}
        onDeleteCancel={() => chat.setDeleteConfirmId(null)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {chat.activeConvId && (
          <div className="px-6 py-3 bg-white border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400" />
              <span className="text-sm font-medium text-navy">
                {chat.conversations.find((c) => c.id === chat.activeConvId)?.title || "Conversation"}
              </span>
            </div>
            <button
              onClick={chat.handleExportAll}
              className="px-3 py-1.5 text-xs text-gray-500 hover:text-navy hover:bg-gray-100 rounded-lg transition-colors"
            >
              Tout exporter
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {chat.showWelcome ? (
            <WelcomeMessage onHintClick={chat.sendMessage} />
          ) : (
            <div className="max-w-3xl mx-auto px-6 py-6 space-y-6">
              {chat.messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  msg={msg}
                  exportingId={chat.exportingId}
                  onExport={chat.handleExportMessage}
                />
              ))}
              {chat.loading && !chat.messages.some((m) => m.id.startsWith("stream-")) && <TypingIndicator />}
              <div ref={chat.messagesEndRef} />
            </div>
          )}
        </div>

        <ChatInputBar
          input={chat.input}
          inputDirection={chat.inputDirection}
          loading={chat.loading}
          inputRef={chat.inputRef}
          onInputChange={chat.handleInputChange}
          onSubmit={(e) => {
            e.preventDefault();
            chat.sendMessage();
          }}
        />
      </div>
    </div>
  );
}
