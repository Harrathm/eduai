import React from "react";
import type { DailyObjective as DailyObjectiveType } from "../api";

interface DailyObjectiveProps {
  objective: DailyObjectiveType;
}

const TYPE_ICONS: Record<string, string> = {
  continue_lesson: "📖",
  start_course: "🚀",
  adaptive_practice: "🎯",
  curriculum_lesson: "📋",
  review: "🔄",
  no_enrollment: "📝",
  no_lessons: "✅",
  no_pending: "🎉",
};

export default function DailyObjective({ objective }: DailyObjectiveProps) {
  const icon = TYPE_ICONS[objective.type] || "📌";

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <h3 className="font-medium text-navy">Objectif du jour</h3>
      </div>
      <p className="text-gray-700 leading-relaxed">{objective.message}</p>
      {objective.estimated_minutes > 0 && (
        <p className="text-sm text-gray-400 mt-2">
          ≈ {objective.estimated_minutes} min
        </p>
      )}
      {objective.lesson_id && (
        <a
          href={
            objective.course_title
              ? `/dashboard/courses/${objective.lesson_id}`
              : "#"
          }
          className="inline-block mt-4 px-5 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy/90 transition-colors"
        >
          Commencer
        </a>
      )}
    </div>
  );
}
