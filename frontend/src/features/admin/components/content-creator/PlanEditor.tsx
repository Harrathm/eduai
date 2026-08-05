import { Sparkles } from "lucide-react";
import type { AIFactoryPlan } from "../../../../api";

type Props = {
  plan: AIFactoryPlan;
  onPlanEdit: (modIdx: number, lesIdx: number | null, field: string, value: string | number) => void;
  setPlan: (p: AIFactoryPlan | null) => void;
  onBack: () => void;
  onStart: () => void;
  countLessons: (p: AIFactoryPlan) => number;
  LEVELS: string[];
  LEVEL_LABELS: Record<string, string>;
};

export function PlanEditor({ plan, onPlanEdit, setPlan, onBack, onStart, countLessons, LEVELS, LEVEL_LABELS }: Props) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-4">
        <h2 className="font-display font-semibold text-navy text-lg">Course Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray mb-1">Title</label>
            <input value={plan.title} onChange={e => setPlan({ ...plan, title: e.target.value })}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray mb-1">Subtitle</label>
            <input value={plan.subtitle} onChange={e => setPlan({ ...plan, subtitle: e.target.value })}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray mb-1">Description</label>
            <textarea value={plan.description} onChange={e => setPlan({ ...plan, description: e.target.value })}
              className="w-full h-24 px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray mb-1">Level</label>
            <select value={plan.level} onChange={e => setPlan({ ...plan, level: e.target.value })}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none">
              {LEVELS.map(l => <option key={l} value={l}>{LEVEL_LABELS[l]}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray mb-1">Category</label>
            <input value={plan.category} onChange={e => setPlan({ ...plan, category: e.target.value })}
              className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
          </div>
        </div>
      </div>

      {plan.modules.map((mod, mi) => (
        <div key={mi} className="bg-white rounded-2xl shadow-sm border border-black/5 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex-1 space-y-2">
              <label className="block text-xs font-medium text-gray">Module {mi + 1} Title</label>
              <input value={mod.title} onChange={e => onPlanEdit(mi, null, "title", e.target.value)}
                className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-orange/20" />
              <textarea value={mod.description} onChange={e => onPlanEdit(mi, null, "description", e.target.value)}
                className="w-full px-4 py-2 bg-cream-m rounded-xl border border-black/5 text-xs focus:outline-none focus:ring-2 focus:ring-orange/20 resize-none h-16" />
            </div>
            <span className="ml-4 text-xs text-gray font-medium">{mod.lessons.length} lessons</span>
          </div>
          <div className="space-y-2 ps-4 border-s-2 border-orange/20">
            {mod.lessons.map((les, li) => (
              <div key={li} className="space-y-1">
                <input value={les.title} onChange={e => onPlanEdit(mi, li, "title", e.target.value)}
                  className="w-full px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-sm focus:outline-none focus:ring-2 focus:ring-orange/20" />
                <div className="flex gap-2">
                  <input value={les.description} onChange={e => onPlanEdit(mi, li, "description", e.target.value)}
                    className="flex-1 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs focus:outline-none focus:ring-2 focus:ring-orange/20" />
                  <input type="number" value={les.duration_minutes} onChange={e => onPlanEdit(mi, li, "duration_minutes", Number(e.target.value))}
                    className="w-20 px-3 py-2 bg-cream-m rounded-lg border border-black/5 text-xs focus:outline-none focus:ring-2 focus:ring-orange/20" title="Minutes" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex justify-end gap-3">
        <button onClick={onBack} className="px-6 py-3 bg-cream-m rounded-xl font-medium text-navy">Back</button>
        <button onClick={onStart} className="px-6 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-semibold flex items-center gap-2 shadow-lg shadow-orange/20">
          <Sparkles className="w-5 h-5" /> Generate All Content ({countLessons(plan)} lessons)
        </button>
      </div>
    </div>
  );
}
