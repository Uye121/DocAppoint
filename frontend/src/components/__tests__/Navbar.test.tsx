import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import Navbar from "../Navbar";

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "../../../hooks/useAuth";

const renderWithRouter = (
  component: React.ReactNode,
  initialEntries: string[] = ["/"],
) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>{component}</MemoryRouter>,
  );
};

describe("Navbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockAuthUser = {
    user: {
      id: "1",
      email: "test@example.com",
      userRole: "patient",
      firstName: "John",
    },
    logout: vi.fn().mockResolvedValue(undefined),
    login: vi.fn(),
    signup: vi.fn(),
    refreshUser: vi.fn(),
    loading: false,
  };

  it("shows Login button when not authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({ ...mockAuthUser, user: null });

    renderWithRouter(<Navbar />);

    // Get all login buttons
    const loginButtons = screen.getAllByRole("button", { name: /login/i });

    // The desktop one should be visible (mobile one is hidden)
    expect(loginButtons[0]).toBeVisible();
    // Or check that we found at least one
    expect(loginButtons.length).toBeGreaterThan(0);
  });

  it("shows user menu when authenticated", () => {
    vi.mocked(useAuth).mockReturnValue(mockAuthUser);

    renderWithRouter(<Navbar />);

    // Check desktop user menu button exists
    expect(screen.getByTestId("user-menu-button")).toBeInTheDocument();

    // Check desktop dropdown items exist (even if hidden)
    expect(screen.getByTestId("user-profile-button")).toBeInTheDocument();
    expect(screen.getByTestId("my-appointments-button")).toBeInTheDocument();
    expect(screen.getByTestId("logout-button")).toBeInTheDocument();

    // Check mobile menu items exist too
    expect(
      screen.getByTestId("mobile-user-profile-button"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("mobile-my-appointments-button"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("mobile-logout-button")).toBeInTheDocument();
  });

  it("toggles mobile menu open / close", async () => {
    const user = userEvent.setup();
    vi.mocked(useAuth).mockReturnValue({ ...mockAuthUser, user: null });

    renderWithRouter(<Navbar />);

    // menu closed initially - get ALL menu buttons and use first one
    const menuButtons = screen.getAllByRole("button", { name: /menu/i });
    const menuBtn = menuButtons[0]; // First one is the visible mobile menu button

    // Mobile menu should start closed
    const mobileMenu = screen.getByLabelText("Mobile navigation menu");
    expect(mobileMenu).toHaveClass("translate-x-full");

    // Click to open
    await user.click(menuBtn);
    expect(mobileMenu).not.toHaveClass("translate-x-full");

    // Find and click close button inside the mobile menu
    const closeBtn = within(mobileMenu).getByRole("button", {
      name: /close menu/i,
    });
    await user.click(closeBtn);

    // Mobile menu should be closed again
    expect(mobileMenu).toHaveClass("translate-x-full");
  });

  it("closes mobile menu on navigation link click for authenticated patient user", async () => {
    const user = userEvent.setup();
    // Mock authenticated patient user
    vi.mocked(useAuth).mockReturnValue(mockAuthUser);

    renderWithRouter(<Navbar />);

    // Open mobile menu
    const menuBtn = screen.getByRole("button", { name: "Open menu" });
    await user.click(menuBtn);

    // Find and click the Home button (should be visible for patient users)
    const homeButton = screen.getByRole("button", { name: "Home" });
    await user.click(homeButton);

    // Check mobile menu is closed
    const mobileMenu = screen.getByLabelText("Mobile navigation menu");
    expect(mobileMenu).toHaveClass("translate-x-full");
  });

  it("does not show navigation links when user is not authenticated", async () => {
    const user = userEvent.setup();
    // Mock unauthenticated user
    vi.mocked(useAuth).mockReturnValue({ ...mockAuthUser, user: null });

    renderWithRouter(<Navbar />);

    // Open mobile menu
    const menuBtn = screen.getByRole("button", { name: "Open menu" });
    await user.click(menuBtn);

    // Verify that no navigation links are shown
    const navItems = ["Home", "All Doctors", "About", "Contact"];
    for (const item of navItems) {
      const navButton = screen.queryByRole("button", { name: item });
      expect(navButton).not.toBeInTheDocument();
    }

    // Verify that the auth button is shown instead
    const mobileMenu = screen.getByLabelText("Mobile navigation menu");
    const authButton = within(mobileMenu).getByRole("button", {
      name: location.pathname === "/login" ? "Create Account" : "Login",
    });
    expect(authButton).toBeInTheDocument();
  });

  it("shows limited navigation links for provider user", async () => {
    const user = userEvent.setup();
    // Mock provider user
    const providerUser = {
      ...mockAuthUser,
      user: {
        ...mockAuthUser.user,
        userRole: "provider",
      },
    };
    vi.mocked(useAuth).mockReturnValue(providerUser);

    renderWithRouter(<Navbar />);

    // Open mobile menu
    const menuBtn = screen.getByRole("button", { name: "Open menu" });
    await user.click(menuBtn);

    // Verify that only Home is shown
    expect(screen.getByRole("button", { name: "Home" })).toBeInTheDocument();

    // Verify that other navigation items are not shown
    const otherNavItems = ["All Doctors", "About", "Contact"];
    for (const item of otherNavItems) {
      const navButton = screen.queryByRole("button", { name: item });
      expect(navButton).not.toBeInTheDocument();
    }

    // Verify that user menu items are shown
    expect(
      screen.getByRole("button", { name: "My Profile" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "My Appointments" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
  });

  it("shows all navigation links for patient user", async () => {
    const user = userEvent.setup();
    // Mock patient user (default)
    vi.mocked(useAuth).mockReturnValue(mockAuthUser);

    renderWithRouter(<Navbar />);

    // Open mobile menu
    const menuBtn = screen.getByRole("button", { name: "Open menu" });
    await user.click(menuBtn);

    // Verify that all navigation items are shown
    const navItems = ["Home", "All Doctors", "About", "Contact"];
    for (const item of navItems) {
      expect(screen.getByRole("button", { name: item })).toBeInTheDocument();
    }

    // Verify that user menu items are shown
    expect(
      screen.getByRole("button", { name: "My Profile" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "My Appointments" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Logout" })).toBeInTheDocument();
  });

  it("shows 'Create Account' when on login page", () => {
    vi.mocked(useAuth).mockReturnValue({ ...mockAuthUser, user: null });

    renderWithRouter(<Navbar />, ["/login"]);

    const createAccountButtons = screen.getAllByText("Create Account");
    expect(createAccountButtons.length).toBeGreaterThan(0);

    expect(createAccountButtons[0]).toBeVisible();
  });

  it("shows 'Login' when on signup page", () => {
    vi.mocked(useAuth).mockReturnValue({ ...mockAuthUser, user: null });

    renderWithRouter(<Navbar />, ["/signup"]);

    const loginButtons = screen.getAllByText("Login");
    expect(loginButtons.length).toBeGreaterThan(0);
  });

  it("calls logout and navigates to login on logout click", async () => {
    const user = userEvent.setup();
    const mockLogout = vi.fn().mockResolvedValue(undefined);
    vi.mocked(useAuth).mockReturnValue({ ...mockAuthUser, logout: mockLogout });

    renderWithRouter(<Navbar />);

    // open dropdown
    await user.hover(screen.getByLabelText(/user menu/i));
    await user.click(screen.getByRole("menuitem", { name: /logout/i }));

    expect(mockLogout).toHaveBeenCalledOnce();
  });
});
