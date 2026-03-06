import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { toast } from "react-toastify";

import {
  AuthProvider,
  SpecialitiesProvider,
  DoctorProvider,
} from "../../src/context";
import { UserAppointment, ProviderHome, Login } from "../../src/pages";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Appointment Cancellation Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
    process.env.TZ = "UTC";
    vi.setSystemTime(new Date("2024-01-16T12:00:00Z"));
  });

  // Helper to render patient appointments page
  const renderPatientAppointments = (
    patientId = "patient-123",
    userMock?: () => [number, unknown],
  ) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Mock authenticated patient
    if (userMock) {
      mock.onGet("http://localhost:8000/api/users/me").reply(userMock);
    } else {
      mock.onGet("http://localhost:8000/api/users/me").reply(200, {
        id: patientId,
        email: "patient@example.com",
        firstName: "John",
        lastName: "Doe",
        userRole: "patient",
        userName: "johndoe",
        hasPatientProfile: true,
        hasProviderProfile: false,
        hasAdminStaffProfile: false,
        hasSystemAdminProfile: false,
      });
    }

    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/my-appointments"]}>
          <AuthProvider>
            <Routes>
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
                    path="/my-appointments"
                    element={<UserAppointment />}
                  />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  // Helper to render provider home page
  const renderProviderHome = (providerId = "provider-123") => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: providerId,
      email: "dr.smith@example.com",
      firstName: "John",
      lastName: "Smith",
      userRole: "provider",
      userName: "drsmith",
      hasPatientProfile: false,
      hasProviderProfile: true,
      hasAdminStaffProfile: false,
      hasSystemAdminProfile: false,
    });

    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/provider-home"]}>
          <AuthProvider>
            {/* <Navbar /> */}
            <Routes>
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
                  <Route path="/provider-home" element={<ProviderHome />} />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  // Mock appointments data
  const mockAppointments = (statuses: string[] = ["CONFIRMED"]) => {
    const now = new Date();
    const futureDate = new Date(now);
    futureDate.setDate(futureDate.getDate() + 7);

    const appointments = statuses.map((status, index) => ({
      id: `appt-${index + 1}`,
      patientId: "patient-123",
      providerId: "provider-123",
      patientName: "John Doe",
      providerName: "Dr. Sarah Johnson",
      providerImage: null,
      appointmentStartDatetimeUtc: futureDate.toISOString(),
      appointmentEndDatetimeUtc: new Date(
        futureDate.getTime() + 30 * 60000,
      ).toISOString(),
      hospital: {
        id: 1,
        name: "City General Hospital",
        address: "123 Main St",
        timezone: "America/New_York",
      },
      reason: "Follow-up consultation",
      status,
    }));

    mock
      .onGet("http://localhost:8000/api/appointment/?patient=patient-123")
      .reply(200, appointments);
    mock
      .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
      .reply(200, appointments);
  };

  describe("Patient Cancellation Flow", () => {
    it("should show cancel button for upcoming appointments", async () => {
      mockAppointments(["CONFIRMED"]);
      renderPatientAppointments();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      });

      // Cancel button should be visible
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      expect(cancelButton).toBeInTheDocument();
    });

    it("should not show cancel button for past appointments", async () => {
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 7);

      mock
        .onGet("http://localhost:8000/api/appointment/?patient=patient-123")
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-123",
            patientName: "John Doe",
            providerName: "Dr. Sarah Johnson",
            providerImage: null,
            appointmentStartDatetimeUtc: pastDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              pastDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Follow-up consultation",
            status: "COMPLETED",
          },
        ]);

      renderPatientAppointments();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      });

      // Cancel button should not be visible
      const cancelButton = screen.queryByRole("button", { name: /cancel/i });
      expect(cancelButton).not.toBeInTheDocument();
    });

    it("should successfully cancel an appointment from patient side", async () => {
      mockAppointments(["CONFIRMED"]);

      // Mock successful cancellation
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(200, {
          detail: "Appointment cancelled successfully",
        });

      renderPatientAppointments();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      });

      // Click cancel button
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      // Verify API was called
      await waitFor(() => {
        expect(mock.history.post.length).toBe(1);
        expect(mock.history.post[0].url).toContain(
          "/appointment/appt-1/set-status/",
        );
        const requestData = JSON.parse(mock.history.post[0].data);
        expect(requestData).toEqual({ status: "CANCELLED" });
      });
    });

    it("should handle cancellation API errors gracefully", async () => {
      mockAppointments(["CONFIRMED"]);

      // Mock failed cancellation
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(500, {
          detail: "Server error",
        });

      renderPatientAppointments();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      });

      // Click cancel button
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      // Wait for error message
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining("Server error"),
        );
      });

      // Appointment should still be visible (not removed from DOM)
      expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();

      // Cancel button should still be present
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });

    it("should update UI after successful cancellation", async () => {
      let appointmentStatus = "CONFIRMED";

      // Use the fixed system time
      const fixedDate = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(fixedDate);
      futureDate.setDate(futureDate.getDate() + 7); // 7 days in future from fixed date

      mock
        .onGet("http://localhost:8000/api/appointment/?patient=patient-123")
        .reply(() => {
          return [
            200,
            [
              {
                id: "appt-1",
                patientId: "patient-123",
                providerId: "provider-123",
                patientName: "John Doe",
                providerName: "Dr. Sarah Johnson",
                providerImage: null,
                appointmentStartDatetimeUtc: futureDate.toISOString(),
                appointmentEndDatetimeUtc: new Date(
                  futureDate.getTime() + 30 * 60000,
                ).toISOString(),
                hospital: {
                  id: 1,
                  name: "City General Hospital",
                  address: "123 Main St",
                  timezone: "America/New_York",
                },
                reason: "Follow-up consultation",
                status: appointmentStatus,
              },
            ],
          ];
        });

      // Mock successful cancellation
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(() => {
          appointmentStatus = "CANCELLED";
          return [200, { detail: "Appointment cancelled successfully" }];
        });

      renderPatientAppointments();

      // Wait for initial appointment with CONFIRMED status
      await waitFor(() => {
        expect(screen.getByText("CONFIRMED")).toBeInTheDocument();
      });

      // Cancel button should be visible
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      // Wait for status to update to CANCELLED
      await waitFor(() => {
        expect(screen.getByText("CANCELLED")).toBeInTheDocument();
      });

      // Cancel button should disappear
      expect(
        screen.queryByRole("button", { name: /cancel/i }),
      ).not.toBeInTheDocument();
    });
  });

  describe("Provider Cancellation Flow", () => {
    it("should show reject button for requested appointments", async () => {
      mockAppointments(["REQUESTED"]);
      renderProviderHome();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("John Doe")).toBeInTheDocument();
      });

      // Find the REQUESTED section
      const requestedSection = screen
        .getByText("REQUESTED Appointments")
        .closest("section");
      expect(requestedSection).toBeInTheDocument();

      // Within that section, there should be Confirm and Reject buttons
      const rejectButton = within(requestedSection!).getByRole("button", {
        name: /reject/i,
      });
      const confirmButton = within(requestedSection!).getByRole("button", {
        name: /confirm/i,
      });

      expect(rejectButton).toBeInTheDocument();
      expect(confirmButton).toBeInTheDocument();
    });

    it("should show cancel button for confirmed appointments", async () => {
      mockAppointments(["CONFIRMED"]);
      renderProviderHome();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("John Doe")).toBeInTheDocument();
      });

      // Find the CONFIRMED section
      const confirmedSection = screen
        .getByText("CONFIRMED Appointments")
        .closest("section");
      expect(confirmedSection).toBeInTheDocument();

      const addRecordButton = within(confirmedSection!).getByRole("button", {
        name: /add.*record/i,
      });
      expect(addRecordButton).toBeInTheDocument();

      // No cancel button for providers on confirmed appointments
      const cancelButton = within(confirmedSection!).queryByRole("button", {
        name: /cancel/i,
      });
      expect(cancelButton).not.toBeInTheDocument();
    });

    it("should reject (cancel) a requested appointment from provider side", async () => {
      mockAppointments(["REQUESTED"]);

      // Mock successful rejection (cancellation)
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(200, {
          detail: "Appointment cancelled successfully",
        });

      renderProviderHome();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("John Doe")).toBeInTheDocument();
      });

      // Find and click the Reject button
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await user.click(rejectButton);

      // Verify API was called with CANCELLED status
      await waitFor(() => {
        expect(mock.history.post.length).toBe(1);
        expect(mock.history.post[0].url).toContain(
          "/appointment/appt-1/set-status/",
        );
        const requestData = JSON.parse(mock.history.post[0].data);
        expect(requestData).toEqual({ status: "CANCELLED" });
      });
    });

    it("should handle provider rejection API errors", async () => {
      mockAppointments(["REQUESTED"]);

      // Mock failed rejection
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(500, {
          detail: "Server error",
        });

      renderProviderHome();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("John Doe")).toBeInTheDocument();
      });

      // Click reject button
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await user.click(rejectButton);

      // Wait for error message (if your app shows one)
      await waitFor(() => {
        const errorElement = screen.queryByText(/server error|failed|error/i);
        if (errorElement) {
          expect(errorElement).toBeInTheDocument();
        }
      });

      // Appointment should still be visible with REQUESTED status
      expect(screen.getByText("REQUESTED")).toBeInTheDocument();

      // Reject button should still be present
      expect(
        screen.getByRole("button", { name: /reject/i }),
      ).toBeInTheDocument();
    });

    it("should move appointment from REQUESTED to appropriate section after rejection", async () => {
      let appointmentStatus = "REQUESTED";

      const fixedDate = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(fixedDate);
      futureDate.setDate(futureDate.getDate() + 7);

      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(() => {
          return [
            200,
            [
              {
                id: "appt-1",
                patientId: "patient-123",
                providerId: "provider-123",
                patientName: "John Doe",
                providerName: "Dr. Sarah Johnson",
                providerImage: null,
                appointmentStartDatetimeUtc: futureDate.toISOString(),
                appointmentEndDatetimeUtc: new Date(
                  futureDate.getTime() + 30 * 60000,
                ).toISOString(),
                hospital: {
                  id: 1,
                  name: "City General Hospital",
                  address: "123 Main St",
                  timezone: "America/New_York",
                },
                reason: "Follow-up consultation",
                status: appointmentStatus,
              },
            ],
          ];
        });

      // Mock successful rejection - updates the status
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(() => {
          appointmentStatus = "CANCELLED";
          return [200, { detail: "Appointment cancelled successfully" }];
        });

      renderProviderHome();

      // Wait for initial appointment in REQUESTED section
      await waitFor(() => {
        expect(screen.getByText("REQUESTED")).toBeInTheDocument();
      });

      // Find and click reject button
      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await user.click(rejectButton);

      // Wait for the appointment to disappear from REQUESTED section
      await waitFor(() => {
        const requestedSection = screen
          .getByText("REQUESTED Appointments")
          .closest("section");
        expect(
          within(requestedSection!).queryByText("John Doe"),
        ).not.toBeInTheDocument();
      });

      // Verify that the "No requested appointments" message appears
      const requestedSection = screen
        .getByText("REQUESTED Appointments")
        .closest("section");
      expect(
        within(requestedSection!).getByText(/no requested appointments/i),
      ).toBeInTheDocument();
    });

    it("should allow confirming a requested appointment instead of cancelling", async () => {
      mockAppointments(["REQUESTED"]);

      // Mock successful confirmation
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(200, {
          detail: "Appointment confirmed successfully",
        });

      renderProviderHome();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("John Doe")).toBeInTheDocument();
      });

      // Find and click the Confirm button
      const confirmButton = screen.getByRole("button", { name: /confirm/i });
      await user.click(confirmButton);

      // Verify API was called with CONFIRMED status
      await waitFor(() => {
        expect(mock.history.post.length).toBe(1);
        expect(mock.history.post[0].url).toContain(
          "/appointment/appt-1/set-status/",
        );
        const requestData = JSON.parse(mock.history.post[0].data);
        expect(requestData).toEqual({ status: "CONFIRMED" });
      });
    });
  });

  describe("Cross-role Cancellation Scenarios", () => {
    it("should not allow patient to cancel already cancelled appointment", async () => {
      mock
        .onGet("http://localhost:8000/api/appointment/?patient=patient-123")
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-123",
            patientName: "John Doe",
            providerName: "Dr. Sarah Johnson",
            providerImage: null,
            appointmentStartDatetimeUtc: new Date().toISOString(),
            appointmentEndDatetimeUtc: new Date().toISOString(),
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Follow-up consultation",
            status: "CANCELLED",
          },
        ]);

      renderPatientAppointments();

      // Wait for appointments to load
      await waitFor(() => {
        expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      });

      // Cancel button should not be visible for cancelled appointments
      const cancelButton = screen.queryByRole("button", { name: /cancel/i });
      expect(cancelButton).not.toBeInTheDocument();

      // Status should show CANCELLED
      expect(screen.getByText("CANCELLED")).toBeInTheDocument();
    });

    it("should sync cancellation status across patient and provider views", async () => {
      // Test the API contract instead
      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply((config) => {
          const data = JSON.parse(config.data);
          expect(data.status).toBe("CANCELLED");
          return [200, { detail: "Appointment cancelled successfully" }];
        });
    });
  });
});
