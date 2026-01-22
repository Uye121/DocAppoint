import { describe, it, expect, vi } from "vitest";
import { renderWithRouter } from "../../../test/utils";
import Navbar from "../Navbar";

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "../../../hooks/useAuth";

describe("Navbar", () => {
  it("shows Login button when not authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({ user: null, logout: vi.fn() });

    const { getByText } = renderWithRouter(<Navbar />);
    expect(getByText("Login")).toBeInTheDocument();
  });

  it("shows user menu when authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, email: "a@b.com", userRole: "patient" },
      logout: vi.fn(),
    });

    const { getByText } = renderWithRouter(<Navbar />);
    expect(getByText("My Profile")).toBeInTheDocument();
  });
});
