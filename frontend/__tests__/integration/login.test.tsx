import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { toast } from "react-toastify";

import {
  AuthProvider,
  DoctorProvider,
  SpecialitiesProvider,
} from "../../src/context";
import { Login, Home, Landing, Signup } from "../../src/pages";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Login Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    return function Wrapper() {
      return (
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={["/login"]}>
            <AuthProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<Landing />} />
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

  it("should successfully log in unassigned user and redirect to onboard", async () => {
    // Mock successful login for unassigned user
    mock.onPost("http://localhost:8000/api/auth/login/").reply(200, {
      user: {
        id: "123",
        email: "test@example.com",
        firstName: "Test",
        lastName: "User",
        userRole: "unassigned",
        userName: "testuser",
        hasPatientProfile: false,
        hasProviderProfile: false,
        hasAdminStaffProfile: false,
        hasSystemAdminProfile: false,
      },
      access: "mock-access-token",
      refresh: "mock-refresh-token",
    });

    render(<Login />, { wrapper: createWrapper() });

    // Fill login form
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "Password123!");
    await user.click(screen.getByRole("button", { name: /login/i }));

    // Verify tokens are stored
    await waitFor(() => {
      expect(localStorage.getItem("access")).toBe("mock-access-token");
      expect(localStorage.getItem("refresh")).toBe("mock-refresh-token");
    });

    await waitFor(() => {
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument();
    });
  });

  it("should successfully log in patient user and redirect to patient home", async () => {
    // Mock successful login for patient
    mock.onPost("http://localhost:8000/api/auth/login/").reply(200, {
      user: {
        id: "123",
        email: "patient@example.com",
        firstName: "Patient",
        lastName: "User",
        userRole: "patient",
        userName: "patientuser",
        hasPatientProfile: true,
        hasProviderProfile: false,
        hasAdminStaffProfile: false,
        hasSystemAdminProfile: false,
      },
      access: "mock-access-token",
      refresh: "mock-refresh-token",
    });

    mock.onGet("http://localhost:8000/api/speciality/").reply(200, [
      { id: 1, name: "Cardiology", image: "cardio.jpg" },
      { id: 2, name: "Dermatology", image: "derma.jpg" },
      { id: 3, name: "Neurology", image: "neuro.jpg" },
    ]);

    mock.onGet("http://localhost:8000/api/provider/").reply(200, [
      {
        id: 1,
        firstName: "John",
        lastName: "Smith",
        specialityName: "Cardiology",
        image: "doctor1.jpg",
      },
      {
        id: 2,
        firstName: "Sarah",
        lastName: "Johnson",
        specialityName: "Dermatology",
        image: "doctor2.jpg",
      },
      {
        id: 3,
        firstName: "Michael",
        lastName: "Chen",
        specialityName: "Neurology",
        image: "doctor3.jpg",
      },
    ]);

    render(<Login />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/email/i), "patient@example.com");
    await user.type(screen.getByLabelText(/password/i), "Password123!");
    await user.click(screen.getByRole("button", { name: /login/i }));

    // Should redirect to patient home
    await waitFor(async () => {
      const bookAppointments = await screen.findAllByText(/book appointment/i);
      expect(bookAppointments.length).toBeGreaterThan(0);
    });

    await waitFor(() => {
      expect(screen.getByText("Cardiology")).toBeInTheDocument();
      expect(screen.getByText("Dermatology")).toBeInTheDocument();
      expect(screen.getByText("Neurology")).toBeInTheDocument();
    });

    // Verify top doctors are displayed
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
      expect(screen.getByText("Sarah Johnson")).toBeInTheDocument();
      expect(screen.getByText("Michael Chen")).toBeInTheDocument();
    });
  });

  it("should show error for invalid credentials", async () => {
    // Mock failed login
    mock.onPost("http://localhost:8000/api/auth/login/").reply(401, {
      detail: "Invalid credentials",
    });

    render(<Login />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/email/i), "wrong@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrongpass");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining("Invalid credentials"),
      );
    });

    // Verify no tokens stored
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("refresh")).toBeNull();

    // Should stay on login page
    expect(screen.getByRole("heading", { name: /login/i })).toBeInTheDocument();
  });

  it("should show error for non-existent user", async () => {
    mock.onPost("http://localhost:8000/api/auth/login/").reply(404, {
      detail: "User not found",
    });

    render(<Login />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/email/i), "nonexistent@example.com");
    await user.type(screen.getByLabelText(/password/i), "password");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining("User not found"),
      );
    });
  });

  it("should handle rate limiting", async () => {
    mock.onPost("http://localhost:8000/api/auth/login/").reply(429, {
      detail: "Too many attempts. Please try again later.",
    });

    render(<Login />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining("try again later"),
      );
    });
  });

  it("should navigate to signup page when clicking create account link", async () => {
    render(<Login />, { wrapper: createWrapper() });

    const createAccountLink = screen.getByText(/here/);
    await user.click(createAccountLink);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /create account/i }),
      ).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
  });
});
