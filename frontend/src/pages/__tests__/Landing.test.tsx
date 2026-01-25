import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Landing from "../Landing";
import { useAuth } from "../../../hooks/useAuth";

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../components/Spinner", () => ({
  default: () => <div data-testid="spinner">Loading...</div>,
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter initialEntries={["/"]}>
    <Routes>
      <Route path="/" element={children} />
      <Route
        path="/login"
        element={<div data-testid="login-page">Login</div>}
      />
      <Route
        path="/patient-home"
        element={<div data-testid="patient-home">Patient Home</div>}
      />
      <Route
        path="/provider-home"
        element={<div data-testid="provider-home">Provider Home</div>}
      />
      <Route
        path="/onboard"
        element={<div data-testid="onboard">Onboard</div>}
      />
    </Routes>
  </MemoryRouter>
);

describe("Landing page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows spinner while loading", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true,
    });

    render(<Landing />, { wrapper: TestWrapper });

    expect(screen.getByTestId("spinner")).toBeInTheDocument();
  });

  it("redirects to login when not authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
    });

    render(<Landing />, { wrapper: TestWrapper });

    expect(screen.getByTestId("login-page")).toBeInTheDocument();
  });

  it("redirects patient to patient-home", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", userRole: "patient" },
      loading: false,
    });

    render(<Landing />, { wrapper: TestWrapper });

    expect(screen.getByTestId("patient-home")).toBeInTheDocument();
  });

  it("redirects provider to provider-home", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "2", userRole: "provider" },
      loading: false,
    });

    render(<Landing />, { wrapper: TestWrapper });

    expect(screen.getByTestId("provider-home")).toBeInTheDocument();
  });

  it("redirects unknown role to onboard", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "3", userRole: "unknown_role" },
      loading: false,
    });

    render(<Landing />, { wrapper: TestWrapper });

    expect(screen.getByTestId("onboard")).toBeInTheDocument();
  });

  it("redirects missing role to onboard", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "4" }, // No userRole property
      loading: false,
    });

    render(<Landing />, { wrapper: TestWrapper });

    expect(screen.getByTestId("onboard")).toBeInTheDocument();
  });
});
