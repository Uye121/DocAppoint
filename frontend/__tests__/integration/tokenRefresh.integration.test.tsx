import React from "react";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  AuthProvider,
  SpecialitiesProvider,
  DoctorProvider,
} from "../../src/context";
import { ProtectedRoutes } from "../../src/components";
import { Home, Login } from "../../src/pages";
import { mock } from "../server";

describe("Token Refresh Flow", () => {
  beforeEach(() => {
    mock.reset();
    localStorage.clear();
    vi.clearAllMocks();
  });

  const standaloneMock = new MockAdapter(axios);

  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    return function Wrapper() {
      return (
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={["/patient-home"]}>
            <AuthProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route element={<ProtectedRoutes />}>
                  <Route
                    path="/patient-home"
                    element={
                      <SpecialitiesProvider>
                        <DoctorProvider>
                          <Home />
                        </DoctorProvider>
                      </SpecialitiesProvider>
                    }
                  />
                </Route>
              </Routes>
            </AuthProvider>
          </MemoryRouter>
        </QueryClientProvider>
      );
    };
  };

  it("should refresh expired token and retry failed request", async () => {
    let refreshCalled = false;
    let getMeCalls = 0;

    // Mock refresh endpoint
    standaloneMock
      .onPost("http://localhost:8000/api/auth/token/refresh/")
      .reply(() => {
        refreshCalled = true;
        return [
          200,
          {
            access: "new-access-token",
            refresh: "new-refresh-token",
          },
        ];
      });

    // Mock getMe endpoint
    mock.onGet("http://localhost:8000/api/users/me").reply(() => {
      getMeCalls += 1;

      if (!refreshCalled && getMeCalls === 1) {
        return [401, { detail: "Token expired" }];
      }
      return [
        200,
        {
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
        },
      ];
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

    // Set expired token in localStorage
    localStorage.setItem("access", "expired-token");
    localStorage.setItem("refresh", "valid-refresh-token");

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <Home />
      </Wrapper>,
    );

    await waitFor(async () => {
      const bookAppointments = await screen.findAllByText(/book appointment/i);
      expect(bookAppointments.length).toBeGreaterThan(0);
    });

    // Verify token was updated
    expect(localStorage.getItem("access")).toBe("new-access-token");
    expect(refreshCalled).toBe(true);
    expect(getMeCalls).toBeGreaterThan(1);

    await waitFor(() => {
      expect(screen.getByText("Cardiology")).toBeInTheDocument();
    });

    // Verify top doctors are displayed
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
    });
  });

  it("should redirect to login if refresh token is invalid", async () => {
    mock.onGet("http://localhost:8000/api/users/me").reply(401, {
      detail: "Token expired",
    });

    standaloneMock
      .onPost("http://localhost:8000/api/auth/token/refresh/")
      .reply(401, {
        detail: "Invalid refresh token",
      });

    localStorage.setItem("access", "expired-token");
    localStorage.setItem("refresh", "invalid-refresh-token");

    render(<Home />, { wrapper: createWrapper() });

    // Should redirect to login
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

  it("should queue multiple requests while refreshing", async () => {
    let refreshCount = 0;
    let getMeCalls = 0;

    // Mock getMe endpoint - fail first, succeed after refresh
    mock.onGet("http://localhost:8000/api/users/me").reply(() => {
      getMeCalls += 1;
      console.log(
        `📞 getMe call #${getMeCalls}, refreshCount: ${refreshCount}`,
      );

      // Always return 401 until refresh happens
      if (refreshCount === 0) {
        return [401, { detail: "Token expired" }];
      }
      return [
        200,
        {
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
        },
      ];
    });

    standaloneMock
      .onPost("http://localhost:8000/api/auth/token/refresh/")
      .reply(() => {
        refreshCount++;
        console.log(`🔥 Refresh endpoint called #${refreshCount}`);
        return [
          200,
          {
            access: "new-access-token",
            refresh: "new-refresh-token",
          },
        ];
      });

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

    localStorage.setItem("access", "expired-token");
    localStorage.setItem("refresh", "valid-refresh-token");

    // Create a component that makes multiple API calls
    function MultiRequestComponent() {
      const [count, setCount] = React.useState(0);

      React.useEffect(() => {
        // Trigger multiple requests in parallel
        Promise.all([
          fetch("/api/users/me"),
          fetch("/api/users/me"),
          fetch("/api/users/me"),
        ]).then(() => setCount(3));
      }, []);

      return (
        <div>
          {count === 3 && <Home />}
          <div data-testid="loading">Loading...</div>
        </div>
      );
    }

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <MultiRequestComponent />
      </Wrapper>,
    );

    // Wait for home page to load
    await waitFor(async () => {
      const bookAppointments = await screen.findAllByText(/book appointment/i);
      expect(bookAppointments.length).toBeGreaterThan(0);
    });

    // Refresh should only be called once despite multiple failed requests
    expect(refreshCount).toBe(1);
    expect(getMeCalls).toBeGreaterThan(1);
    expect(localStorage.getItem("access")).toBe("new-access-token");
  });
});
