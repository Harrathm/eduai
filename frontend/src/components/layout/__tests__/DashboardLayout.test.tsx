/**
 * Tests for DashboardLayout: Context Switcher, Impersonation Banner, UpsellModal.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DashboardLayout from "../DashboardLayout";
import UpsellModal, { triggerUpsell, setUpsellHandler } from "../../UpsellModal";
import { useAuthStore } from "../../../store/authStore";

// Mock the auth store
vi.mock("../../../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

// Mock child components
vi.mock("../WalletWidget", () => ({
  default: () => <div data-testid="wallet-widget" />,
}));

vi.mock("../LanguageSelector", () => ({
  default: () => <div data-testid="language-selector" />,
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Outlet: () => <div data-testid="outlet" />,
  };
});

describe("DashboardLayout", () => {
  const mockSwitchRole = vi.fn();
  const mockStopImpersonation = vi.fn();
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as any).mockReturnValue({
      user: {
        id: 1,
        email: "test@test.com",
        full_name: "Test User",
        role: "admin_school",
        roles: ["admin_school", "pedagogical_lead"],
        activeRole: "admin_school",
        school_id: 1,
      },
      logout: mockLogout,
      switchRole: mockSwitchRole,
      stopImpersonation: mockStopImpersonation,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Context Switcher", () => {
    it("shows role switcher when user has multiple roles", () => {
      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Should show the role switcher button
      const switcherButton = screen.getByText(/Admin École/i);
      expect(switcherButton).toBeTruthy();
    });

    it("does not show role switcher when user has single role", () => {
      (useAuthStore as any).mockReturnValue({
        user: {
          id: 1,
          email: "test@test.com",
          full_name: "Test User",
          role: "student",
          roles: ["student"],
          activeRole: "student",
          school_id: 1,
        },
        logout: mockLogout,
        switchRole: mockSwitchRole,
        stopImpersonation: mockStopImpersonation,
      });

      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Should not show the role switcher
      expect(screen.queryByText(/Sélectionner un rôle/i)).toBeNull();
    });

    it("shows all roles in dropdown when opened", async () => {
      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Click the role switcher button
      const switcherButton = screen.getByText(/Admin École/i);
      fireEvent.click(switcherButton);

      // Should show both roles
      await waitFor(() => {
        expect(screen.getByText(/Admin École/i)).toBeTruthy();
        expect(screen.getByText(/Responsable Pédagogique/i)).toBeTruthy();
      });
    });

    it("calls switchRole when a different role is selected", async () => {
      mockSwitchRole.mockResolvedValue(true);

      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Open dropdown
      const switcherButton = screen.getByText(/Admin École/i);
      fireEvent.click(switcherButton);

      // Click on the other role
      await waitFor(() => {
        const otherRole = screen.getByText(/Responsable Pédagogique/i);
        fireEvent.click(otherRole);
      });

      expect(mockSwitchRole).toHaveBeenCalledWith("pedagogical_lead");
    });
  });

  describe("Impersonation Banner", () => {
    it("shows banner when user is impersonated", () => {
      (useAuthStore as any).mockReturnValue({
        user: {
          id: 101,
          email: "target@test.com",
          full_name: "Target User",
          role: "student",
          roles: ["student"],
          activeRole: "student",
          school_id: 1,
          impersonated_by: 42,
        },
        logout: mockLogout,
        switchRole: mockSwitchRole,
        stopImpersonation: mockStopImpersonation,
      });

      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Should show the impersonation banner
      expect(screen.getByText(/Mode Impersonation actif/i)).toBeTruthy();
      expect(screen.getByText(/Target User/i)).toBeTruthy();
    });

    it("does not show banner when user is not impersonated", () => {
      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Should not show the impersonation banner
      expect(screen.queryByText(/Mode Impersonation actif/i)).toBeNull();
    });

    it("calls stopImpersonation when button is clicked", async () => {
      mockStopImpersonation.mockResolvedValue(true);

      (useAuthStore as any).mockReturnValue({
        user: {
          id: 101,
          email: "target@test.com",
          full_name: "Target User",
          role: "student",
          roles: ["student"],
          activeRole: "student",
          school_id: 1,
          impersonated_by: 42,
        },
        logout: mockLogout,
        switchRole: mockSwitchRole,
        stopImpersonation: mockStopImpersonation,
      });

      render(
        <MemoryRouter>
          <DashboardLayout />
        </MemoryRouter>
      );

      // Click stop impersonation button
      const stopButton = screen.getByText(/Arrêter l'impersonation/i);
      fireEvent.click(stopButton);

      expect(mockStopImpersonation).toHaveBeenCalled();
    });
  });
});

describe("UpsellModal", () => {
  it("renders when isOpen is true", () => {
    render(
      <UpsellModal
        isOpen={true}
        onClose={vi.fn()}
        requiredPack="Silver"
      />
    );

    expect(screen.getByText(/Contenu Premium/i)).toBeTruthy();
    expect(screen.getByText(/Silver/i)).toBeTruthy();
  });

  it("does not render when isOpen is false", () => {
    render(
      <UpsellModal
        isOpen={false}
        onClose={vi.fn()}
        requiredPack="Silver"
      />
    );

    expect(screen.queryByText(/Contenu Premium/i)).toBeNull();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <UpsellModal
        isOpen={true}
        onClose={onClose}
        requiredPack="Silver"
      />
    );

    const laterButton = screen.getByText(/Plus tard/i);
    fireEvent.click(laterButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("navigates to packs when upgrade button is clicked", () => {
    render(
      <UpsellModal
        isOpen={true}
        onClose={vi.fn()}
        requiredPack="Silver"
      />
    );

    const upgradeButton = screen.getByText(/Voir les packs/i);
    fireEvent.click(upgradeButton);

    expect(mockNavigate).toHaveBeenCalledWith("/dashboard/packs");
  });
});

describe("API Client 402 Handling", () => {
  it("triggerUpsell calls the registered handler", () => {
    const handler = vi.fn();
    setUpsellHandler(handler);

    triggerUpsell("Test message", "Gold");

    expect(handler).toHaveBeenCalledWith("Test message", "Gold");
  });
});
