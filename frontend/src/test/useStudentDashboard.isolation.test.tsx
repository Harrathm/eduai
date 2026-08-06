/**
 * Tests d'isolation réels — Hook useStudentDashboard
 *
 * Chaque test mock UN SEUL endpoint en échec 500,
 * les 5 autres retournent des données valides.
 * On vérifie que le hook retourne toujours les données des sources qui réussissent.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";

// ── Données de test ────────────────────────────────────────────────

const VALID_DASHBOARD = {
  tier: "decouverte",
  user_id: 1,
  total_enrolled_courses: 2,
  overall_progress_pct: 45,
  lessons_completed: 5,
  total_lessons: 12,
  courses: [
    { id: 1, title: "Maths", niveau_scolaire: "9eme de base", progress_pct: 60, lessons_completed: 3, total_lessons: 5 },
    { id: 2, title: "Francais", niveau_scolaire: "9eme de base", progress_pct: 30, lessons_completed: 2, total_lessons: 7 },
  ],
  daily_objective: { tier: "decouverte", type: "review", message: "Continue!", estimated_minutes: 15 },
  features: { ai_access: "basic", placement_test: true, recommendations: "basic", analytics: false },
  niveau_scolaire: "9eme de base",
};

const VALID_ABONNEMENTS = [
  { id: 1, pack_id: 1, statut: "actif", tier: "gratuit", start_date: "2026-09-15", end_date: "2027-06-19", status: "active" },
];

const VALID_WALLET = { total_dt: 150, total_tokens: 50, pools: [{ pool: "purchased", dt: 100, tokens: 30 }] };

const VALID_INBOX = [
  { id: 1, sender_name: "Admin", subject: "Bienvenue", is_read: false, content: "Hello", created_at: "", sender_id: 1, recipient_id: 2 },
];

const VALID_SOFT_SKILLS = [
  { id: 10, title: "Communication", category: "soft_skills" },
];

const VALID_PACKS = [
  { id: 1, nom: "Pack Basique", tier: "basique", prix_tnd: 50, description: "Pack basique", niveau_scolaire: "9eme de base" },
];

const ERROR_500 = new Error("500 Internal Server Error");

// ── Mock API calls ─────────────────────────────────────────────────

const mockDashboard = vi.fn();
const mockMesAbonnements = vi.fn();
const mockBalance = vi.fn();
const mockInboxList = vi.fn();
const mockCatalogList = vi.fn();
const mockListPacks = vi.fn();

vi.mock("../features/student/hooks/useTrimesterReconfiguration", () => ({
  useTrimesterReconfiguration: () => ({
    currentTrimester: { label: "T1", number: 1, startDate: new Date("2026-09-15"), endDate: new Date("2026-12-19") },
    isInReconfigWindow: false, daysRemainingInWindow: 0, isEligible: false, isGolden: false, isFree: true,
    alreadyReconfigured: false, canReconfigure: false, loading: false, error: null, refresh: vi.fn(),
  }),
}));

// Mock the API module with our controllable mocks
vi.mock("@/api", () => ({
  tierApi: { dashboard: (...args: any[]) => mockDashboard(...args) },
  abonnementApi: { mesAbonnements: (...args: any[]) => mockMesAbonnements(...args), listPacks: (...args: any[]) => mockListPacks(...args) },
  walletApi: { balance: (...args: any[]) => mockBalance(...args) },
  inboxApi: { list: (...args: any[]) => mockInboxList(...args) },
  catalogApi: { list: (...args: any[]) => mockCatalogList(...args) },
}));

// ── Import hook AFTER mocks ────────────────────────────────────────

import { useStudentDashboard } from "../features/student/hooks/useStudentDashboard";

function wrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

describe("Dashboard widget isolation — 6 sources (hook level)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDashboard.mockResolvedValue(VALID_DASHBOARD);
    mockMesAbonnements.mockResolvedValue(VALID_ABONNEMENTS);
    mockBalance.mockResolvedValue(VALID_WALLET);
    mockInboxList.mockResolvedValue(VALID_INBOX);
    mockCatalogList.mockResolvedValue(VALID_SOFT_SKILLS);
    mockListPacks.mockResolvedValue(VALID_PACKS);
  });

  it("source 1/6: dashboard fails → other 5 sources still loaded", async () => {
    mockDashboard.mockRejectedValueOnce(ERROR_500);

    const { result } = renderHook(() => useStudentDashboard(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Dashboard failed
    expect(result.current.dashboard).toBeNull();
    expect(result.current.sourceErrors.dashboard).toBe("500 Internal Server Error");

    // Other 5 sources loaded successfully
    expect(result.current.abonnement).toEqual(VALID_ABONNEMENTS[0]);
    expect(result.current.sourceErrors.abonnement).toBeNull();
    expect(result.current.wallet).toEqual(VALID_WALLET);
    expect(result.current.sourceErrors.wallet).toBeNull();
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.sourceErrors.inbox).toBeNull();
    expect(result.current.softSkillsCourses).toHaveLength(1);
    expect(result.current.sourceErrors.softSkills).toBeNull();
    expect(result.current.availablePacks).toHaveLength(1);
    expect(result.current.sourceErrors.packs).toBeNull();
  });

  it("source 2/6: abonnement fails → dashboard and other 4 loaded", async () => {
    mockMesAbonnements.mockRejectedValueOnce(ERROR_500);

    const { result } = renderHook(() => useStudentDashboard(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Abonnement failed
    expect(result.current.abonnement).toBeNull();
    expect(result.current.packTier).toBeNull();
    expect(result.current.sourceErrors.abonnement).toBe("500 Internal Server Error");

    // Other 5 sources loaded
    expect(result.current.dashboard).toEqual(VALID_DASHBOARD);
    expect(result.current.sourceErrors.dashboard).toBeNull();
    expect(result.current.wallet).toEqual(VALID_WALLET);
    expect(result.current.sourceErrors.wallet).toBeNull();
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.sourceErrors.inbox).toBeNull();
    expect(result.current.softSkillsCourses).toHaveLength(1);
    expect(result.current.sourceErrors.softSkills).toBeNull();
    expect(result.current.availablePacks).toHaveLength(1);
    expect(result.current.sourceErrors.packs).toBeNull();
  });

  it("source 3/6: wallet fails → dashboard, abonnement, inbox, soft, packs loaded", async () => {
    mockBalance.mockRejectedValueOnce(ERROR_500);

    const { result } = renderHook(() => useStudentDashboard(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Wallet failed
    expect(result.current.wallet).toBeNull();
    expect(result.current.sourceErrors.wallet).toBe("500 Internal Server Error");

    // Other 5 sources loaded
    expect(result.current.dashboard).toEqual(VALID_DASHBOARD);
    expect(result.current.sourceErrors.dashboard).toBeNull();
    expect(result.current.abonnement).toEqual(VALID_ABONNEMENTS[0]);
    expect(result.current.sourceErrors.abonnement).toBeNull();
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.sourceErrors.inbox).toBeNull();
    expect(result.current.softSkillsCourses).toHaveLength(1);
    expect(result.current.sourceErrors.softSkills).toBeNull();
    expect(result.current.availablePacks).toHaveLength(1);
    expect(result.current.sourceErrors.packs).toBeNull();
  });

  it("source 4/6: inbox fails → dashboard, abonnement, wallet, soft, packs loaded", async () => {
    mockInboxList.mockRejectedValueOnce(ERROR_500);

    const { result } = renderHook(() => useStudentDashboard(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Inbox failed
    expect(result.current.unreadCount).toBe(0);
    expect(result.current.lastMessage).toBeNull();
    expect(result.current.sourceErrors.inbox).toBe("500 Internal Server Error");

    // Other 5 sources loaded
    expect(result.current.dashboard).toEqual(VALID_DASHBOARD);
    expect(result.current.sourceErrors.dashboard).toBeNull();
    expect(result.current.abonnement).toEqual(VALID_ABONNEMENTS[0]);
    expect(result.current.sourceErrors.abonnement).toBeNull();
    expect(result.current.wallet).toEqual(VALID_WALLET);
    expect(result.current.sourceErrors.wallet).toBeNull();
    expect(result.current.softSkillsCourses).toHaveLength(1);
    expect(result.current.sourceErrors.softSkills).toBeNull();
    expect(result.current.availablePacks).toHaveLength(1);
    expect(result.current.sourceErrors.packs).toBeNull();
  });

  it("source 5/6: softSkills fails → dashboard, abonnement, wallet, inbox, packs loaded", async () => {
    mockCatalogList.mockRejectedValueOnce(ERROR_500);

    const { result } = renderHook(() => useStudentDashboard(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Soft skills failed
    expect(result.current.softSkillsCourses).toHaveLength(0);
    expect(result.current.sourceErrors.softSkills).toBe("500 Internal Server Error");

    // Other 5 sources loaded
    expect(result.current.dashboard).toEqual(VALID_DASHBOARD);
    expect(result.current.sourceErrors.dashboard).toBeNull();
    expect(result.current.abonnement).toEqual(VALID_ABONNEMENTS[0]);
    expect(result.current.sourceErrors.abonnement).toBeNull();
    expect(result.current.wallet).toEqual(VALID_WALLET);
    expect(result.current.sourceErrors.wallet).toBeNull();
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.sourceErrors.inbox).toBeNull();
    expect(result.current.availablePacks).toHaveLength(1);
    expect(result.current.sourceErrors.packs).toBeNull();
  });

  it("source 6/6: packs fails → dashboard, abonnement, wallet, inbox, softSkills loaded", async () => {
    mockListPacks.mockRejectedValueOnce(ERROR_500);

    const { result } = renderHook(() => useStudentDashboard(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Packs failed
    expect(result.current.availablePacks).toHaveLength(0);
    expect(result.current.sourceErrors.packs).toBe("500 Internal Server Error");

    // Other 5 sources loaded
    expect(result.current.dashboard).toEqual(VALID_DASHBOARD);
    expect(result.current.sourceErrors.dashboard).toBeNull();
    expect(result.current.abonnement).toEqual(VALID_ABONNEMENTS[0]);
    expect(result.current.sourceErrors.abonnement).toBeNull();
    expect(result.current.wallet).toEqual(VALID_WALLET);
    expect(result.current.sourceErrors.wallet).toBeNull();
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.sourceErrors.inbox).toBeNull();
    expect(result.current.softSkillsCourses).toHaveLength(1);
    expect(result.current.sourceErrors.softSkills).toBeNull();
  });
});
