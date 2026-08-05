import { Sparkles } from "lucide-react";
import { CONTEXT_HINTS } from "../../hooks/useAIChat";

type Props = {
  onHintClick: (hint: string) => void;
};

export function WelcomeMessage({ onHintClick }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange to-orange-l flex items-center justify-center mb-6 shadow-or">
        <Sparkles className="w-8 h-8 text-white" />
      </div>
      <h2 className="text-2xl font-semibold text-navy mb-2 font-body">
        Bonjour ! Je suis votre tuteur IA
      </h2>
      <p className="text-gray-500 text-center max-w-md mb-8 leading-relaxed">
        Posez-moi des questions sur vos cours, demandez des explications,
        des résumés ou des exercices.
      </p>
      <div className="grid grid-cols-2 gap-3 max-w-lg">
        {CONTEXT_HINTS.map((hint, i) => (
          <button
            key={i}
            onClick={() => onHintClick(hint)}
            className="text-start px-4 py-3 text-sm bg-white border border-gray-100 rounded-xl hover:border-orange/30 hover:bg-orange-p text-gray-600 hover:text-navy transition-all duration-200 shadow-sm"
          >
            {hint}
          </button>
        ))}
      </div>
    </div>
  );
}
