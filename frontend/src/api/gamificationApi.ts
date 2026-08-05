/**
 * Gamification API — badges, streak, rankings.
 * Extracted from inline fetch calls in GamificationPage.tsx.
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface Badge {
  id: number;
  name: string;
  description: string;
  icon_url: string | null;
  category: string;
  earned_at: string | null;
  is_earned: boolean;
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
}

export interface Ranking {
  user_id: number;
  full_name: string;
  points: number;
  rank: number;
}

// ─── Endpoints ──────────────────────────────────────────────────────────────

export const gamificationApi = {
  badges: () => api.get<Badge[]>("/api/gamification/badges"),

  streak: () => api.get<Streak>("/api/gamification/streak"),

  rankings: () => api.get<Ranking[]>("/api/gamification/rankings"),
};
