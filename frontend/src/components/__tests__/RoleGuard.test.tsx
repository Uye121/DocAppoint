import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import type { Location } from "react-router-dom";
import RoleGuard from "../RoleGuard";
import { useAuth } from "../../../hooks/useAuth";
import type { AuthCtx } from "../../types/auth";

vi.mock("../../../hooks/useAuth");
vi.mock("react-router-dom", async () => ({
  ...(await vi.importActual("react-router-dom")),
  useLocation: vi.fn(),
  Navigate: ({ to }: { to: string }) => <div>Navigate to {to}</div>,
}));

// Mock the Spinner component
vi.mock("../Spinner", () => ({
  default: () => <div data-testid="spinner">Loading...</div>,
}));

describe("RoleGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useLocation).mockReturnValue({
      pathname: "/test",
      search: "",
      hash: "",
      state: null,
      key: "default",
    } as Location);
  });

  it("renders children when user role is allowed", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { userRole: "patient" },
      loading: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    } as AuthCtx);

    render(
      <MemoryRouter>
        <RoleGuard allowed={["patient"]}>
          <span>Protected content</span>
        </RoleGuard>
      </MemoryRouter>,
    );

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects to login when user is null", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    } as AuthCtx);

    render(
      <MemoryRouter>
        <RoleGuard allowed={["patient"]}>
          <span>Protected content</span>
        </RoleGuard>
      </MemoryRouter>,
    );

    expect(screen.getByText("Navigate to /login")).toBeInTheDocument();
  });

  it("redirects to root when role is not allowed", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { userRole: "provider" },
      loading: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    } as AuthCtx);

    render(
      <MemoryRouter>
        <RoleGuard allowed={["patient"]}>
          <span>Protected content</span>
        </RoleGuard>
      </MemoryRouter>,
    );

    expect(screen.getByText("Navigate to /")).toBeInTheDocument();
  });

  it("shows spinner while loading", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    } as AuthCtx);

    render(
      <MemoryRouter>
        <RoleGuard allowed={["patient"]}>
          <span>Protected content</span>
        </RoleGuard>
      </MemoryRouter>,
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });
});
