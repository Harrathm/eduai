/**
 * Wallet API — balance, history, purchase, admin operations.
 * Enriched from existing wallet.ts (was 18 lines, now full-featured).
 */

import { api } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────

export interface WalletPool {
  type: string;
  balance: number;
  currency: string;
  expires_at: string | null;
  source: string;
}

export interface WalletBalance {
  total_dt: number;
  total_tokens: number;
  pools: WalletPool[];
}

export interface WalletTransaction {
  id: number;
  type: string;
  amount: number;
  currency: string;
  description: string | null;
  pool: string | null;
  created_at: string;
}

export interface WalletHistoryResponse {
  total: number;
  page: number;
  page_size: number;
  items: WalletTransaction[];
}

export interface PurchaseResult {
  checkout_url: string;
  session_id: string;
}

export interface WalletEntry {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  school_id: number;
  school_name: string;
  balance_dt: number;
  balance_tokens: number;
  total_dt_spent: number;
  total_tokens_spent: number;
  is_active: boolean;
}

export interface WalletAdjustResult {
  id: number;
  email: string;
  balance_dt: number;
  balance_tokens: number;
  action: string;
  amount_dt: number;
  amount_tokens: number;
  reason: string;
  admin_id: number;
  timestamp: string;
}

// ─── Student/Parent Wallet API ──────────────────────────────────────────────

export const walletApi = {
  balance: () => api.get<WalletBalance>("/api/wallet/balance"),

  history: (page = 1, pageSize = 20) =>
    api.get<WalletHistoryResponse>(
      `/api/wallet/history?page=${page}&page_size=${pageSize}`
    ),

  purchase: (months: 1 | 3 | 12) =>
    api.post<PurchaseResult>("/api/wallet/purchase", { months }),
};

// ─── Admin Wallet API ───────────────────────────────────────────────────────

export const walletAdmin = {
  list: (params?: {
    school_id?: number;
    role?: string;
    skip?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.school_id) sp.set("school_id", String(params.school_id));
    if (params?.role) sp.set("role", params.role);
    if (params?.skip) sp.set("skip", String(params.skip));
    if (params?.limit) sp.set("limit", String(params.limit));
    const qs = sp.toString();
    return api.get<{ total: number; items: WalletEntry[] }>(
      `/api/admin/wallets${qs ? `?${qs}` : ""}`
    );
  },

  add: (userId: number, amountTokens: number, amountDt: number, reason: string) =>
    api.post<WalletAdjustResult>(`/api/admin/wallets/${userId}/add`, {
      amount_dt: amountDt,
      amount_tokens: amountTokens,
      reason,
    }),

  deduct: (userId: number, amountTokens: number, amountDt: number, reason: string) =>
    api.post<WalletAdjustResult>(`/api/admin/wallets/${userId}/deduct`, {
      amount_dt: amountDt,
      amount_tokens: amountTokens,
      reason,
    }),
};
