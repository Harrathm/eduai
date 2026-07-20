/**
 * Module API pour le portefeuille de crédits
 * Utilise le client API centralisé pour la gestion de l'authentification
 */

import { api } from "../utils/apiClient";

export async function getWalletBalance() {
  return api.get("/api/wallet/balance");
}

export async function getWalletHistory(page = 1, pageSize = 20) {
  return api.get(`/api/wallet/history?page=${page}&page_size=${pageSize}`);
}

export async function purchaseCredits(months: number) {
  return api.post("/api/wallet/purchase", { months });
}
