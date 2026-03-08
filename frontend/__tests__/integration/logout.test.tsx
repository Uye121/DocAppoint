import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  AuthProvider,
  SpecialitiesProvider,
  DoctorProvider,
} from "../../src/context";
import { Login, Home, Landing, Signup } from "../../src/pages";
import { Navbar, ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

const standaloneMock = new MockAdapter(axios);

describe("Logout Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    standaloneMock.reset();
    localStorage.clear();
  });

  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    return function Wrapper() {
      return (
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={["/patient-home"]}>
            <AuthProvider>
              <Navbar />
              <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route element={<ProtectedRoutes />}>
                  <Route
                    element={
                      <SpecialitiesProvider>
                        <DoctorProvider>
                          <Outlet />
                        </DoctorProvider>
                      </SpecialitiesProvider>
                    }
                  >
                    <Route
                      path="/onboard"
                      element={<div>complete your profile</div>}
                    />
                    <Route path="/patient-home" element={<Home />} />
                  </Route>
                </Route>
              </Routes>
            </AuthProvider>
          </MemoryRouter>
        </QueryClientProvider>
      );
    };
  };

  it("should successfully log out and clear tokens", async () => {
    mock.onPost("http://localhost:8000/api/auth/logout/").reply(200, {
      detail: "Logged out successfully",
    });

    // Set initial authenticated state
    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: "123",
      email: "test@example.com",
      firstName: "Test",
      lastName: "User",
      userRole: "patient",
      userName: "testuser",
      hasPatientProfile: true,
      hasProviderProfile: false,
      hasAdminStaffProfile: false,
      hasSystemAdminProfile: false,
    });

    render(<Home />, { wrapper: createWrapper() });

    const userMenuButton = await screen.findByTestId("user-menu-button");
    await user.click(userMenuButton);

    // Find and click logout button
    const logoutButton = await screen.findByTestId("logout-button");
    await user.click(logoutButton);

    // Should redirect to login and show actual Login component
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    // Verify tokens were cleared
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("refresh")).toBeNull();
  });

  it("should handle logout when no refresh token exists", async () => {
    localStorage.setItem("access", "valid-token");

    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: "123",
      email: "test@example.com",
      firstName: "Test",
      lastName: "User",
      userRole: "patient",
      userName: "testuser",
      hasPatientProfile: true,
      hasProviderProfile: false,
      hasAdminStaffProfile: false,
      hasSystemAdminProfile: false,
    });

    // Mock specialities and doctors for Home page
    mock
      .onGet("http://localhost:8000/api/speciality/")
      .reply(200, [{ id: 1, name: "Cardiology", image: "cardio.jpg" }]);

    mock.onGet("http://localhost:8000/api/provider/").reply(200, [
      {
        id: 1,
        firstName: "John",
        lastName: "Smith",
        specialityName: "Cardiology",
        image: "doctor1.jpg",
      },
    ]);

    const Wrapper = createWrapper("/patient-home");

    // Render a component that includes both Navbar and Home
    function TestPage() {
      return (
        <>
          <Navbar />
          <Home />
        </>
      );
    }

    render(
      <Wrapper>
        <TestPage />
      </Wrapper>,
    );

    // Wait for Home to load and user to be authenticated
    await waitFor(async () => {
      const bookAppointments = await screen.findAllByText(/book appointment/i);
      expect(bookAppointments.length).toBeGreaterThan(0);
    });

    // Find and click user menu to open dropdown
    const userMenuButton = await screen.findByTestId("user-menu-button");
    await user.click(userMenuButton);

    // Find and click logout button
    const logoutButton = await screen.findByTestId("logout-button");
    await user.click(logoutButton);

    // Should redirect to login
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });

    // Verify tokens were cleared
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("refresh")).toBeNull();

    // No API call should be made since no refresh token
    expect(standaloneMock.history.post.length).toBe(0);
  });

  it("should clear tokens even if logout API fails", async () => {
    mock.onPost("http://localhost:8000/api/auth/logout/").reply(500, {
      detail: "Server error",
    });

    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: "123",
      email: "test@example.com",
      firstName: "Test",
      lastName: "User",
      userRole: "patient",
      userName: "testuser",
      hasPatientProfile: true,
      hasProviderProfile: false,
      hasAdminStaffProfile: false,
      hasSystemAdminProfile: false,
    });

    // Mock specialities and doctors for Home page
    mock
      .onGet("http://localhost:8000/api/speciality/")
      .reply(200, [{ id: 1, name: "Cardiology", image: "cardio.jpg" }]);

    mock.onGet("http://localhost:8000/api/provider/").reply(200, [
      {
        id: 1,
        firstName: "John",
        lastName: "Smith",
        specialityName: "Cardiology",
        image: "doctor1.jpg",
      },
    ]);

    const Wrapper = createWrapper("/patient-home");

    // Render a component that includes both Navbar and Home
    function TestPage() {
      return (
        <>
          <Navbar />
          <Home />
        </>
      );
    }

    render(
      <Wrapper>
        <TestPage />
      </Wrapper>,
    );

    // Wait for Home to load and user to be authenticated
    await waitFor(async () => {
      const bookAppointments = await screen.findAllByText(/book appointment/i);
      expect(bookAppointments.length).toBeGreaterThan(0);
    });

    // Find and click user menu to open dropdown
    const userMenuButton = await screen.findByTestId("user-menu-button");
    await user.click(userMenuButton);

    // Find and click logout button
    const logoutButton = await screen.findByTestId("logout-button");
    await user.click(logoutButton);

    // Should still clear tokens and redirect to login despite API error
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });

    // Verify tokens were cleared
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("refresh")).toBeNull();

    // Verify the logout API was called (even though it failed)
    expect(mock.history.post.length).toBe(1);
    expect(mock.history.post[0].url).toContain("/auth/logout/");
  });

  it("should redirect to login when accessing protected route after logout", async () => {
    // Set initial authenticated state
    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: "123",
      email: "test@example.com",
      firstName: "Test",
      lastName: "User",
      userRole: "patient",
      userName: "testuser",
      hasPatientProfile: true,
      hasProviderProfile: false,
      hasAdminStaffProfile: false,
      hasSystemAdminProfile: false,
    });

    // Mock specialities and doctors for Home page
    mock
      .onGet("http://localhost:8000/api/speciality/")
      .reply(200, [{ id: 1, name: "Cardiology", image: "cardio.jpg" }]);

    mock.onGet("http://localhost:8000/api/provider/").reply(200, [
      {
        id: 1,
        firstName: "John",
        lastName: "Smith",
        specialityName: "Cardiology",
        image: "doctor1.jpg",
      },
    ]);

    const Wrapper = createWrapper("/patient-home");

    function TestPage() {
      return (
        <>
          <Navbar />
          <Home />
        </>
      );
    }

    render(
      <Wrapper>
        <TestPage />
      </Wrapper>,
    );

    // Verify home page loads
    await waitFor(async () => {
      const bookAppointments = await screen.findAllByText(/book appointment/i);
      expect(bookAppointments.length).toBeGreaterThan(0);
    });

    // Find and click user menu to open dropdown
    const userMenuButton = await screen.findByTestId("user-menu-button");
    await user.click(userMenuButton);

    // Find and click logout button
    const logoutButton = await screen.findByTestId("logout-button");
    await user.click(logoutButton);

    // Should redirect to login
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });

    // Verify tokens were cleared
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("refresh")).toBeNull();

    // Simulate using back button
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });

    // Simulate user clicking browser back button
    window.history.back();

    // Should stay on login or redirect back to login
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });
  });
});
