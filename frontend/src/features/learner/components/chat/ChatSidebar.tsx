import { Plus, MessageSquare, Trash2, Search, Clock } from "lucide-react";
import type { ConversationSummary } from "../../../../api";
import { formatTime } from "../../hooks/useAIChat";
import { Button } from "@/components/ui";

type Props = {
  conversations: ConversationSummary[];
  activeConvId: number | null;
  searchQuery: string;
  deleteConfirmId: number | null;
  onSearchChange: (v: string) => void;
  onStartNew: () => void;
  onOpenConversation: (id: number) => void;
  onDeleteConfirmToggle: (id: number) => void;
  onDelete: (id: number) => void;
  onDeleteCancel: () => void;
};

export function ChatSidebar({
  conversations, activeConvId, searchQuery, deleteConfirmId,
  onSearchChange, onStartNew, onOpenConversation,
  onDeleteConfirmToggle, onDelete, onDeleteCancel,
}: Props) {
  return (
    <aside className="w-80 bg-white border-r border-gray-100 flex flex-col flex-shrink-0">
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange to-orange-l flex items-center justify-center shadow-sm">
            <MessageSquare className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-navy text-sm">Assistant IA</h2>
            <p className="text-xs text-gray-400">Tuteur personnel</p>
          </div>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={onStartNew}
        >
          <Plus className="w-4 h-4" />
          Nouvelle conversation
        </Button>
      </div>

      <div className="px-4 py-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Rechercher..."
            className="w-full ps-9 pe-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange/20 focus:border-orange/40 transition-all"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
          Récent
        </p>
        <div className="space-y-0.5">
          {conversations.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-6">
              {searchQuery ? "Aucun résultat" : "Aucune conversation"}
            </p>
          )}
          {conversations.slice(0, 20).map((conv) => (
            <div key={conv.id} className="group relative">
              <Button
                variant="ghost"
                size="md"
                onClick={() => onOpenConversation(conv.id)}
              >
                <p className={`text-sm truncate ${activeConvId === conv.id ? "text-orange font-medium" : "text-gray-700"}`}>
                  {conv.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className="text-[10px] text-gray-400">
                    {formatTime(conv.updated_at)}
                  </span>
                  {conv.message_count > 0 && (
                    <>
                      <span className="text-[10px] text-gray-300">&middot;</span>
                      <span className="text-[10px] text-gray-400">
                        {conv.message_count} msg
                      </span>
                    </>
                  )}
                </div>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConfirmToggle(conv.id);
                }}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
              {deleteConfirmId === conv.id && (
                <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-dp p-2 z-10 flex gap-1.5">
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onDelete(conv.id)}
                  >
                    Supprimer
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onDeleteCancel}
                  >
                    Annuler
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
