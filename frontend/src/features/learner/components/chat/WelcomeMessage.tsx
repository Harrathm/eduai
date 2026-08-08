import { Sparkles } from "lucide-react";
import { CONTEXT_HINTS } from "../../hooks/useAIChat";
import { Button } from "@/components/ui";

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
          <Button
            key={i}
            variant="ghost"
            size="sm"
            onClick={() => onHintClick(hint)}
          >
            {hint}
          </Button>
        ))}
      </div>
    </div>
  );
}
