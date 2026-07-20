import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup, act } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import StudentCourseCatalog from "@/features/student/pages/CourseCatalog";

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

describe("StudentCourseCatalog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  const mockCourses = [
    {
      id: 1,
      title: "Introduction à Python",
      description: "Cours pour débutants",
      teacher_name: "Prof. Martin",
      duration_hours: 10,
      price: 50,
      price_tokens: 50,
      price_dt: 25,
      enrolled_count: 150,
    },
    {
      id: 2,
      title: "Advanced JavaScript",
      description: "Formation avancée",
      teacher_name: "Prof. Dupont",
      duration_hours: 20,
      price: 100,
      price_tokens: 100,
      price_dt: 50,
      enrolled_count: 80,
    },
  ];

  it("renders loading state initially", async () => {
    mockFetch.mockImplementationOnce(() => new Promise(() => {}));
    mockFetch.mockImplementationOnce(() => new Promise(() => {}));

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });
    expect(screen.getByText("Chargement...")).toBeInTheDocument();
  });

  it("renders course catalog heading", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockCourses) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /course catalog/i })).toBeInTheDocument();
    });
  });

  it("renders courses when loaded", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockCourses) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Introduction à Python")).toBeInTheDocument();
      expect(screen.getByText("Advanced JavaScript")).toBeInTheDocument();
    });
  });

  it("renders empty state when no courses", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Aucun cours trouvé")).toBeInTheDocument();
    });
  });

  it("renders course details (teacher, duration, price)", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockCourses[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Prof. Martin")).toBeInTheDocument();
      expect(screen.getByText("10h")).toBeInTheDocument();
      expect(screen.getByText("50 TND")).toBeInTheDocument();
    });
  });

  it("shows enrolled button for already enrolled courses", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockCourses[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([{ id: 1 }]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Inscrit")).toBeInTheDocument();
    });
  });

  it("shows enroll button for free non-enrolled courses", async () => {
    const freeCourses = [{ ...mockCourses[0], price: 0 }];
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(freeCourses) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("S'inscrire")).toBeInTheDocument();
    });
  });

  it("shows buy button for paid non-enrolled courses", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([mockCourses[0]]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Acheter")).toBeInTheDocument();
    });
  });

  it("filters courses by search term", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockCourses) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });

    await waitFor(() => {
      expect(screen.getByText("Introduction à Python")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Rechercher un cours...");

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: "Python" } });
    });

    await waitFor(() => {
      expect(screen.getByText("Introduction à Python")).toBeInTheDocument();
      expect(screen.queryByText("Advanced JavaScript")).not.toBeInTheDocument();
    });
  });

  it("renders search input", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });
    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    render(<StudentCourseCatalog />, { wrapper: BrowserRouter });
    expect(screen.getByPlaceholderText("Rechercher un cours...")).toBeInTheDocument();
  });
});