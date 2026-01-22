import { describe, it, expect, vi } from "vitest";
import { renderWithRouter } from "../../../test/utils";
import ProtectedRoutes from "../ProtectedRoutes";

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "../../../hooks/useAuth";
const mockUseAuth = vi.mocked(useAuth);

describe("ProtectedRoutes", () => {
  it("redirects to /login when not authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
    });

    const { getByText } = renderWithRouter(<ProtectedRoutes />, {
      path: "/doctors",
    });
    expect(getByText("login")).toBeInTheDocument();
  });

  it("redirects unassigned user to /onboard", () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        email: "a@b.com",
        userRole: "unassigned",
      },
      loading: false,
    });

    const { getByText } = renderWithRouter(<ProtectedRoutes />, {
      path: "/app",
    });
    expect(getByText("onboard")).toBeInTheDocument();
  });
});
