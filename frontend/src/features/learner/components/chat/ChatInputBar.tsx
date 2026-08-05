import { Send } from "lucide-react";

type Props = {
  input: string;
  inputDirection: "ltr" | "rtl";
  loading: boolean;
  inputRef: React.RefObject<HTMLInputElement>;
  onInputChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
};

export function ChatInputBar({ input, inputDirection, loading, inputRef, onInputChange, onSubmit }: Props) {
  return (
    <div className="p-4 bg-white border-t border-gray-100">
      <form onSubmit={onSubmit} className="max-w-3xl mx-auto">
        <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-2 focus-within:border-orange/40 focus-within:ring-2 focus-within:ring-orange/10 transition-all">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={inputDirection === "rtl" ? "اكتب سؤالك هنا..." : "Posez une question à votre tuteur IA..."}
            dir={inputDirection}
            disabled={loading}
            className="flex-1 bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none disabled:opacity-50 py-1"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="w-9 h-9 flex items-center justify-center bg-gradient-to-r from-orange to-orange-l text-white rounded-xl hover:shadow-or disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-gray-400 text-center mt-2">
          L'IA peut faire des erreurs. Vérifiez les informations importantes.
        </p>
      </form>
    </div>
  );
}
