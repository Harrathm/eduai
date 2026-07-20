import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup, act } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import LoginPage from "@/features/auth/pages/LoginPage";

vi.mock("@/store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
    (useAuthStore as ReturnType<typeof vi.fn>).mockReturnValue({
      token: null,
      user: null,
      login: vi.fn(),
      isLoading: false,
      error: null,
    });
  });

  it("renders login form with email and password inputs", () => {
    render(<LoginPage />, { wrapper: BrowserRouter });
    expect(screen.getByPlaceholderText("vous@ecole.edu")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /se connecter/i })).toBeInTheDocument();
  });

  it("shows welcome text", () => {
    render(<LoginPage />, { wrapper: BrowserRouter });
    expect(screen.getByText("Bienvenue")).toBeInTheDocument();
    expect(screen.getByText("Connectez-vous pour continuer")).toBeInTheDocument();
  });

  it("allows typing in email and password fields", () => {
    render(<LoginPage />, { wrapper: BrowserRouter });
    const emailInput = screen.getByPlaceholderText("vous@ecole.edu") as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText("••••••••") as HTMLInputElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });

    expect(emailInput.value).toBe("test@example.com");
    expect(passwordInput.value).toBe("password123");
  });

  it("calls login on form submit", async () => {
    const mockLogin = vi.fn().mockResolvedValue(true);
    (useAuthStore as ReturnType<typeof vi.fn>).mockReturnValue({
      token: null,
      user: null,
      login: mockLogin,
      isLoading: false,
      error: null,
    });

    render(<LoginPage />, { wrapper: BrowserRouter });

    const emailInput = screen.getByPlaceholderText("vous@ecole.edu");
    const passwordInput = screen.getByPlaceholderText("••••••••");
    const button = screen.getByRole("button", { name: /se connecter/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });

    await act(async () => {
      fireEvent.click(button);
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("test@example.com", "password123");
    });
  });

  it("shows error message when error is present", () => {
    (useAuthStore as ReturnType<typeof vi.fn>).mockReturnValue({
      token: null,
      user: null,
      login: vi.fn(),
      isLoading: false,
      error: "Identifiants incorrects",
    });

    render(<LoginPage />, { wrapper: BrowserRouter });
    expect(screen.getByText("Identifiants incorrects")).toBeInTheDocument();
  });

  it("shows loading state when isLoading is true", () => {
    (useAuthStore as ReturnType<typeof vi.fn>).mockReturnValue({
      token: null,
      user: null,
      login: vi.fn(),
      isLoading: true,
      error: null,
    });

    render(<LoginPage />, { wrapper: BrowserRouter });
    expect(screen.getByText("Connexion...")).toBeInTheDocument();
  });

  it("disables submit button when loading", () => {
    (useAuthStore as ReturnType<typeof vi.fn>).mockReturnValue({
      token: null,
      user: null,
      login: vi.fn(),
      isLoading: true,
      error: null,
    });

    render(<LoginPage />, { wrapper: BrowserRouter });
    expect(screen.getByRole("button", { name: /connexion\.\.\./i })).toBeDisabled();
  });

  it("renders EDUAI branding", () => {
    render(<LoginPage />, { wrapper: BrowserRouter });
    expect(screen.getByText(/eduai/i)).toBeInTheDocument();
  });
});