import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup, act } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import MyLearning from "@/features/teacher/pages/MyLearning";

const mockFetch = vi.fn();
global.fetch = mockFetch;

vi.mock("@/store/authStore", () => ({
  useAuthStore: vi.fn(() => ({
    token: "test-token",
    user: null,
    login: vi.fn(),
    isLoading: false,
    error: null,
  })),
}));

describe("MyLearning", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  const mockTrainings = [
    {
      id: 1,
      title: "Pédagogie moderne",
      description: "Introduction aux méthodes pédagogiques",
      teacher_name: "Prof. Martin",
      duration_hours: 15,
      price_tokens: 75,
      price_dt: 40,
      enrolled_count: 45,
      category: "pedagogy",
    },
    {
      id: 2,
      title: "Technologie en classe",
      description: "Outils numériques pour enseignants",
      teacher_name: "Prof. Sophie",
      duration_hours: 20,
      price_tokens: 100,
      price_dt: 55,
      enrolled_count: 30,
      category: "technology",
    },
  ];

  it("renders page heading", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockTrainings) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /mon.*apprentissage/i })).toBeInTheDocument();
    });
  });

  it("renders loading state initially", () => {
    mockFetch.mockImplementationOnce(() => new Promise(() => {}));
    mockFetch.mockImplementationOnce(() => new Promise(() => {}));

    render(<MyLearning />, { wrapper: BrowserRouter });
    expect(screen.getByText("Chargement...")).toBeInTheDocument();
  });

  it("renders empty state when no trainings", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Aucune formation trouvée")).toBeInTheDocument();
    });
  });

  it("renders trainings list when loaded", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockTrainings) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Pédagogie moderne")).toBeInTheDocument();
      expect(screen.getByText("Technologie en classe")).toBeInTheDocument();
    });
  });

  it("shows enrolled section with no enrollments", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText(/mes formations inscrites/i)).toBeInTheDocument();
      expect(screen.getByText("Aucune inscription")).toBeInTheDocument();
    });
  });

  it("shows enrolled trainings in enrolled section", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockTrainings[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([{ course_id: 1 }]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getAllByText("Pédagogie moderne").length).toBeGreaterThan(0);
      expect(screen.getByText(/mes formations inscrites/i)).toBeInTheDocument();
    });
  });

  it("renders training details (teacher, duration, price, enrolled count)", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockTrainings[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Prof. Martin")).toBeInTheDocument();
      expect(screen.getByText("15h")).toBeInTheDocument();
      expect(screen.getByText("45 inscrits")).toBeInTheDocument();
      expect(screen.getByText(/75.*tokens/i)).toBeInTheDocument();
      expect(screen.getByText("40 DT")).toBeInTheDocument();
    });
  });

  it("shows Commencer button for enrolled trainings", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockTrainings[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([{ course_id: 1 }]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Commencer")).toBeInTheDocument();
    });
  });

  it("shows S'inscrire button for non-enrolled trainings", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockTrainings[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("S'inscrire")).toBeInTheDocument();
    });
  });

  it("filters trainings by search term", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockTrainings) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Pédagogie moderne")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Rechercher une formation...");

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: "Technologie" } });
    });

    await waitFor(() => {
      expect(screen.getByText("Technologie en classe")).toBeInTheDocument();
      expect(screen.queryByText("Pédagogie moderne")).not.toBeInTheDocument();
    });
  });

  it("renders category filter", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByText("Toutes catégories")).toBeInTheDocument();
  });

  it("filters by category", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockTrainings) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<MyLearning />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Pédagogie moderne")).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox") as HTMLSelectElement;

    await act(async () => {
      fireEvent.change(select, { target: { value: "pedagogy" } });
    });

    await waitFor(() => {
      expect(screen.getByText("Pédagogie moderne")).toBeInTheDocument();
      expect(screen.queryByText("Technologie en classe")).not.toBeInTheDocument();
    });
  });
});