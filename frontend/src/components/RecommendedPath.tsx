import React from "react";
import type { RecommendedPath as RecommendedPathType } from "../api";
import TierBadge from "./TierBadge";

interface RecommendedPathProps {
  path: RecommendedPathType;
}

export default function RecommendedPath({ path }: RecommendedPathProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-navy">Mon Parcours</h3>
        <TierBadge tier={path.tier} size="sm" />
      </div>
      <p className="text-sm text-gray-500 mb-4">{path.description}</p>

      {path.courses.length > 0 ? (
        <div className="space-y-3">
          {path.courses.map((c) => (
            <a
              key={c.id}
              href={`/dashboard/courses/${c.id}`}
              className="block p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-navy text-sm">{c.title}</span>
                <span className="text-xs text-gray-400">
                  {Math.round(c.progress_pct)}%
                </span>
              </div>
              <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-orange rounded-full transition-all"
                  style={{ width: `${c.progress_pct}%` }}
                />
              </div>
            </a>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-400 italic">
          Pas encore de cours inscrits
        </p>
      )}

      <div className="mt-4 p-3 bg-blue-50 rounded-xl">
        <p className="text-sm text-blue-700">
          <span className="font-medium">Prochaine étape :</span> {path.next_step}
        </p>
      </div>

      {path.weakest_subject && (
        <div className="mt-3 p-3 bg-orange-50 rounded-xl">
          <p className="text-sm text-orange-700">
            <span className="font-medium">À renforcer :</span> {path.weakest_subject}
          </p>
        </div>
      )}
    </div>
  );
}
