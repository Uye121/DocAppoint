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
import { PatientOnboard, Home, Login, Landing } from "../../src/pages";
import { ProtectedRoutes, RoleGuard } from "../../src/components";
import { mock } from "../server";

describe("Patient Onboarding Flow", () => {
  const user = userEvent.setup();
  let userRole = "unassigned";

  beforeEach(() => {
    mock.reset();
    userRole = "unassigned";
  });

  const renderOnboardPage = (
    initialPath = "/onboard",
    userMock?: () => [number, unknown],
  ) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Mock authenticated user with unassigned role
    if (userMock) {
      mock.onGet("http://localhost:8000/api/users/me").reply(userMock);
    } else {
      mock.onGet("http://localhost:8000/api/users/me").reply(() => {
        if (userRole === "patient") {
          return [
            200,
            {
              id: "patient-123",
              email: "new@example.com",
              firstName: "New",
              lastName: "User",
              userRole: "patient",
              userName: "newuser",
              hasPatientProfile: false,
              hasProviderProfile: false,
              hasAdminStaffProfile: false,
              hasSystemAdminProfile: false,
            },
          ];
        }
        return [
          200,
          {
            id: "patient-123",
            email: "new@example.com",
            firstName: "New",
            lastName: "User",
            userRole: "unassigned",
            userName: "newuser",
            hasPatientProfile: false,
            hasProviderProfile: false,
            hasAdminStaffProfile: false,
            hasSystemAdminProfile: false,
          },
        ];
      });
    }

    // Set tokens
    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
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
                    path="/patient-home"
                    element={
                      <RoleGuard allowed={["patient"]}>
                        <Home />
                      </RoleGuard>
                    }
                  />
                  <Route path="/onboard" element={<PatientOnboard />} />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it("should successfully submit onboarding form with all fields", async () => {
    // Mock successful onboarding
    mock.onPost("http://localhost:8000/api/patient/onboard/").reply(() => {
      userRole = "patient";
      return [
        201,
        {
          id: "patient-123",
          bloodType: "O+",
          insurance: "Blue Cross",
          weight: 70,
          height: 175,
          allergies: "Pollen, Peanuts",
          chronicConditions: "Asthma",
          currentMedications: "Inhaler",
        },
      ];
    });

    // Mock doctors and specialities for home page
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

    renderOnboardPage("/onboard");

    await waitFor(() => {
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument();
    });

    // Fill all form fields
    await user.type(screen.getByLabelText(/blood type/i), "O+");
    await user.type(screen.getByLabelText(/insurance/i), "Blue Cross");
    await user.type(screen.getByLabelText(/weight/i), "70");
    await user.type(screen.getByLabelText(/height/i), "175");
    await user.type(screen.getByLabelText(/allergies/i), "Pollen, Peanuts");
    await user.type(screen.getByLabelText(/chronic conditions/i), "Asthma");
    await user.type(screen.getByLabelText(/current medications/i), "Inhaler");

    // Submit form
    const saveButton = screen.getByRole("button", { name: /save profile/i });
    await user.click(saveButton);

    // Verify API was called with correct data
    await waitFor(() => {
      expect(mock.history.post.length).toBe(1);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData).toMatchObject({
        bloodType: "O+",
        insurance: "Blue Cross",
        weight: 70,
        height: 175,
        allergies: "Pollen, Peanuts",
        chronicConditions: "Asthma",
        currentMedications: "Inhaler",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("patient-home")).toBeInTheDocument();
    });
  });

  it("should submit onboarding form with minimal fields (optional fields)", async () => {
    // Mock successful onboarding with minimal data
    mock.onPost("http://localhost:8000/api/patient/onboard/").reply(() => {
      userRole = "patient";
      return [
        201,
        {
          id: "patient-123",
        },
      ];
    });

    // Mock doctors and specialities for home page
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

    renderOnboardPage("/onboard");

    await waitFor(() => {
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument();
    });

    // Submit form without filling any fields
    const saveButton = screen.getByRole("button", { name: /save profile/i });
    await user.click(saveButton);

    // Verify API was called with empty object
    await waitFor(() => {
      expect(mock.history.post.length).toBe(1);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData).toEqual({});
    });

    // Should redirect to patient home
    await waitFor(() => {
      expect(screen.getByTestId("patient-home")).toBeInTheDocument();
    });
  });

  it("should handle API errors during onboarding", async () => {
    // Mock failed onboarding
    mock.onPost("http://localhost:8000/api/patient/onboard/").reply(500, {
      detail: "Server error",
    });

    renderOnboardPage("/onboard");

    await waitFor(() => {
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument();
    });

    // Fill and submit form
    await user.type(screen.getByLabelText(/blood type/i), "O+");
    const saveButton = screen.getByRole("button", { name: /save profile/i });
    await user.click(saveButton);

    // Should show error message (if implemented) or stay on page
    await waitFor(() => {
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument();
    });

    // Should not redirect
    expect(screen.queryByText(/book appointment/i)).not.toBeInTheDocument();
  });

  it("should validate numeric fields", async () => {
    renderOnboardPage("/onboard");

    await waitFor(() => {
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument();
    });

    const weightInput = screen.getByLabelText(/weight/i);
    const heightInput = screen.getByLabelText(/height/i);

    // Try to enter non-numeric values
    await user.type(weightInput, "abc");
    await user.type(heightInput, "xyz");

    // Should not accept non-numeric input (HTML5 number inputs handle this)
    expect(weightInput).toHaveValue(null);
    expect(heightInput).toHaveValue(null);

    // Enter valid numbers
    await user.type(weightInput, "70");
    await user.type(heightInput, "175");

    expect(weightInput).toHaveValue(70);
    expect(heightInput).toHaveValue(175);
  });

  it("should navigate to home if user is already onboarded", async () => {
    userRole = "patient";
    // Mock doctors and specialities for home page
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

    renderOnboardPage("/onboard");

    // Should redirect to patient home
    await waitFor(() => {
      expect(screen.getByTestId("patient-home")).toBeInTheDocument();
    });

    // Onboard page should not be visible
    expect(
      screen.queryByText(/complete your profile/i),
    ).not.toBeInTheDocument();
  });

  it("should navigate to login if not authenticated", async () => {
    renderOnboardPage("/onboard", () => [401, { detail: "Unauthorized" }]);

    // Should redirect to login
    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });
});
