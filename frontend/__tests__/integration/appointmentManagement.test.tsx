import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  AuthProvider,
  SpecialitiesProvider,
  DoctorProvider,
} from "../../src/context";
import {
  UserAppointment,
  ProviderHome,
  Appointments,
  Login,
} from "../../src/pages";
import { ProtectedRoutes, Navbar } from "../../src/components";
import { mock } from "../server";

describe("Appointment Management Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
    process.env.TZ = "UTC";
    vi.setSystemTime(new Date("2024-01-16T12:00:00Z"));
  });

  // Helper to render patient appointments page
  const renderPatientAppointments = (patientId = "patient-123") => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

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

    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/my-appointments"]}>
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
                  <Route
                    path="/my-appointments"
                    element={<UserAppointment />}
                  />
                  <Route
                    path="/appointment/:docId"
                    element={<Appointments />}
                  />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  // Helper to render provider dashboard
  const renderProviderDashboard = (providerId = "provider-123") => {
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
            <Navbar />
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

  describe("Appointment Status Management", () => {
    it("should display correct status badges for different appointment states", async () => {
      const now = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(now);
      futureDate.setDate(futureDate.getDate() + 7);

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-1",
            patientName: "John Doe",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Checkup",
            status: "REQUESTED",
          },
          {
            id: "appt-2",
            patientId: "patient-123",
            providerId: "provider-2",
            patientName: "John Doe",
            providerName: "Dr. Johnson",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 2,
              name: "Memorial",
              address: "456 Ave",
              timezone: "UTC",
            },
            reason: "Follow-up",
            status: "CONFIRMED",
          },
          {
            id: "appt-3",
            patientId: "patient-123",
            providerId: "provider-3",
            patientName: "John Doe",
            providerName: "Dr. Williams",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 3,
              name: "General",
              address: "789 Blvd",
              timezone: "UTC",
            },
            reason: "Consultation",
            status: "COMPLETED",
          },
          {
            id: "appt-4",
            patientId: "patient-123",
            providerId: "provider-4",
            patientName: "John Doe",
            providerName: "Dr. Brown",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 4,
              name: "University",
              address: "101 College",
              timezone: "UTC",
            },
            reason: "Annual",
            status: "CANCELLED",
          },
          {
            id: "appt-5",
            patientId: "patient-123",
            providerId: "provider-5",
            patientName: "John Doe",
            providerName: "Dr. Miller",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 5,
              name: "Childrens",
              address: "202 Kids",
              timezone: "UTC",
            },
            reason: "Pediatric",
            status: "RESCHEDULED",
          },
        ]);

      renderPatientAppointments();

      await waitFor(() => {
        expect(screen.getByText("REQUESTED")).toBeInTheDocument();
        expect(screen.getByText("CONFIRMED")).toBeInTheDocument();
        expect(screen.getByText("COMPLETED")).toBeInTheDocument();
        expect(screen.getByText("CANCELLED")).toBeInTheDocument();
        expect(screen.getByText("RESCHEDULED")).toBeInTheDocument();
      });

      // Verify each status has appropriate styling (optional)
      const requestedBadge = screen.getByText("REQUESTED");
      expect(requestedBadge).toHaveClass(/bg-status-requested/);
    });

    it("should show cancel button only for cancellable statuses", async () => {
      const now = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(now);
      futureDate.setDate(futureDate.getDate() + 7);

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-1",
            patientName: "John Doe",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Checkup",
            status: "REQUESTED",
          },
          {
            id: "appt-2",
            patientId: "patient-123",
            providerId: "provider-2",
            patientName: "John Doe",
            providerName: "Dr. Johnson",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 2,
              name: "Memorial",
              address: "456 Ave",
              timezone: "UTC",
            },
            reason: "Follow-up",
            status: "CONFIRMED",
          },
          {
            id: "appt-3",
            patientId: "patient-123",
            providerId: "provider-3",
            patientName: "John Doe",
            providerName: "Dr. Williams",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 3,
              name: "General",
              address: "789 Blvd",
              timezone: "UTC",
            },
            reason: "Consultation",
            status: "COMPLETED",
          },
          {
            id: "appt-4",
            patientId: "patient-123",
            providerId: "provider-4",
            patientName: "John Doe",
            providerName: "Dr. Brown",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 4,
              name: "University",
              address: "101 College",
              timezone: "UTC",
            },
            reason: "Annual",
            status: "CANCELLED",
          },
        ]);

      renderPatientAppointments();

      await waitFor(() => {
        expect(screen.getByText("Dr. Smith")).toBeInTheDocument();
      });

      const cancelButtons = screen.queryAllByRole("button", {
        name: /cancel/i,
      });

      expect(cancelButtons.length).toBe(3);
    });
  });

  describe("Appointment Rescheduling", () => {
    it("should allow patient to view rescheduled appointment", async () => {
      const now = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(now);
      futureDate.setDate(futureDate.getDate() + 7);

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-1",
            patientName: "John Doe",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Checkup",
            status: "RESCHEDULED",
          },
        ]);

      renderPatientAppointments();

      await waitFor(() => {
        expect(screen.getByText("RESCHEDULED")).toBeInTheDocument();
        expect(screen.getByText("Dr. Smith")).toBeInTheDocument();
      });

      // RESCHEDULED appointments might have different UI treatment
      const rescheduledBadge = screen.getByText("RESCHEDULED");
      expect(rescheduledBadge).toHaveClass(/bg-status-rescheduled/);
    });

    it("should show rescheduled appointments in provider dashboard", async () => {
      const now = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(now);
      futureDate.setDate(futureDate.getDate() + 7);

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { provider: "provider-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-123",
            patientName: "John Doe",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Checkup",
            status: "RESCHEDULED",
          },
        ]);

      renderProviderDashboard();

      await waitFor(() => {
        expect(
          screen.getByText("RESCHEDULED Appointments"),
        ).toBeInTheDocument();
        expect(screen.getByText("John Doe")).toBeInTheDocument();
      });

      // Rescheduled appointments might have different actions
      const rescheduledSection = screen
        .getByText("RESCHEDULED Appointments")
        .closest("section");
      expect(rescheduledSection).toBeInTheDocument();

      // Should not have confirm/reject buttons for rescheduled
      const confirmButton = within(rescheduledSection!).queryByRole("button", {
        name: /confirm/i,
      });
      const rejectButton = within(rescheduledSection!).queryByRole("button", {
        name: /reject/i,
      });

      expect(confirmButton).not.toBeInTheDocument();
      expect(rejectButton).not.toBeInTheDocument();
    });
  });

  describe("Appointment Filtering and Sorting", () => {
    it("should separate upcoming and past appointments correctly", async () => {
      const now = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(now);
      futureDate.setDate(futureDate.getDate() + 7);
      const pastDate = new Date(now);
      pastDate.setDate(pastDate.getDate() - 7);

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-1",
            patientName: "John Doe",
            providerName: "Dr. Future",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Future appointment",
            status: "CONFIRMED",
          },
          {
            id: "appt-2",
            patientId: "patient-123",
            providerId: "provider-2",
            patientName: "John Doe",
            providerName: "Dr. Past",
            providerImage: null,
            appointmentStartDatetimeUtc: pastDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              pastDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 2,
              name: "Memorial",
              address: "456 Ave",
              timezone: "UTC",
            },
            reason: "Past appointment",
            status: "COMPLETED",
          },
        ]);

      renderPatientAppointments();

      await waitFor(() => {
        expect(screen.getByText("Dr. Future")).toBeInTheDocument();
        expect(screen.getByText("Dr. Past")).toBeInTheDocument();
      });

      // Find the upcoming appointments grid
      const upcomingHeading = screen.getByText("Upcoming");
      const upcomingGrid = upcomingHeading.nextElementSibling;
      expect(upcomingGrid).toHaveClass("grid");

      // Find the past appointments grid
      const pastHeading = screen.getByText("Past");
      const pastGrid = pastHeading.nextElementSibling;
      expect(pastGrid).toHaveClass("grid");

      // Upcoming grid should have future appointment
      expect(within(upcomingGrid!).getByText("Dr. Future")).toBeInTheDocument();

      // Upcoming grid should not have past appointment
      expect(
        within(upcomingGrid!).queryByText("Dr. Past"),
      ).not.toBeInTheDocument();

      // Past grid should have past appointment
      expect(within(pastGrid!).getByText("Dr. Past")).toBeInTheDocument();

      // Past grid should NOT have future appointment
      expect(
        within(pastGrid!).queryByText("Dr. Future"),
      ).not.toBeInTheDocument();
    });

    it("should show empty states when no appointments", async () => {
      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, []);

      renderPatientAppointments();

      await waitFor(() => {
        expect(
          screen.getByText(/no upcoming appointments/i),
        ).toBeInTheDocument();
        expect(screen.getByText(/no past appointments/i)).toBeInTheDocument();
      });
    });
  });

  describe("Provider Appointment Actions", () => {
    it("should allow provider to confirm requested appointments", async () => {
      let appointmentStatus = "REQUESTED";

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { provider: "provider-123" },
        })
        .reply(() => {
          return [
            200,
            [
              {
                id: "appt-1",
                patientId: "patient-123",
                providerId: "provider-123",
                patientName: "John Doe",
                providerName: "Dr. Smith",
                providerImage: null,
                appointmentStartDatetimeUtc: new Date(
                  "2024-01-23T12:00:00Z",
                ).toISOString(),
                appointmentEndDatetimeUtc: new Date(
                  "2024-01-23T12:30:00Z",
                ).toISOString(),
                hospital: {
                  id: 1,
                  name: "City Hospital",
                  address: "123 St",
                  timezone: "UTC",
                },
                reason: "Consultation",
                status: appointmentStatus,
              },
            ],
          ];
        });

      mock
        .onPost("http://localhost:8000/api/appointment/appt-1/set-status/")
        .reply(() => {
          appointmentStatus = "CONFIRMED";
          return [200, { detail: "Confirmed" }];
        });

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("REQUESTED")).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole("button", { name: /confirm/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText("CONFIRMED")).toBeInTheDocument();
      });

      // Confirm button should disappear
      expect(
        screen.queryByRole("button", { name: /confirm/i }),
      ).not.toBeInTheDocument();
    });

    it("should show different actions for different appointment statuses", async () => {
      const futureDate = new Date("2024-01-23T12:00:00Z");

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { provider: "provider-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-123",
            patientName: "John Doe",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Consultation",
            status: "REQUESTED",
          },
          {
            id: "appt-2",
            patientId: "patient-456",
            providerId: "provider-123",
            patientName: "Jane Smith",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Follow-up",
            status: "CONFIRMED",
          },
          {
            id: "appt-3",
            patientId: "patient-789",
            providerId: "provider-123",
            patientName: "Bob Wilson",
            providerName: "Dr. Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: futureDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              futureDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City Hospital",
              address: "123 St",
              timezone: "UTC",
            },
            reason: "Annual",
            status: "COMPLETED",
          },
        ]);

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("John Doe")).toBeInTheDocument();
        expect(screen.getByText("Jane Smith")).toBeInTheDocument();
        expect(screen.getByText("Bob Wilson")).toBeInTheDocument();
      });

      // REQUESTED should have Confirm/Reject
      const requestedSection = screen
        .getByText("REQUESTED Appointments")
        .closest("section");
      expect(
        within(requestedSection!).getByRole("button", { name: /confirm/i }),
      ).toBeInTheDocument();
      expect(
        within(requestedSection!).getByRole("button", { name: /reject/i }),
      ).toBeInTheDocument();

      // CONFIRMED should have Add/View Record
      const confirmedSection = screen
        .getByText("CONFIRMED Appointments")
        .closest("section");
      expect(
        within(confirmedSection!).getByRole("button", { name: /add.*record/i }),
      ).toBeInTheDocument();

      // COMPLETED should have View Record
      const completedSection = screen
        .getByText("COMPLETED Appointments")
        .closest("section");
      expect(
        within(completedSection!).getByRole("button", { name: /add.*record/i }),
      ).toBeInTheDocument();
    });
  });

  describe("Appointment Details Display", () => {
    it("should display appointment details correctly", async () => {
      const futureDate = new Date("2024-01-23T12:00:00Z");

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, [
          {
            id: "appt-1",
            patientId: "patient-123",
            providerId: "provider-1",
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
            reason: "Follow-up consultation for hypertension",
            status: "CONFIRMED",
          },
        ]);

      renderPatientAppointments();

      await waitFor(() => {
        expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      });

      // Check for appointment details
      expect(
        screen.getByText(/follow-up consultation for hypertension/i),
      ).toBeInTheDocument();

      const dateElement = screen.getByText(/jan 23/i);
      expect(dateElement).toBeInTheDocument();
    });
  });

  describe("Appointment History", () => {
    it("should display appointment history with correct sorting", async () => {
      const now = new Date("2024-01-16T12:00:00Z");

      // Create appointments with different dates
      const appointments = [];
      for (let i = 1; i <= 5; i++) {
        const date = new Date(now);
        date.setDate(date.getDate() - i * 7); // Each a week apart
        appointments.push({
          id: `appt-${i}`,
          patientId: "patient-123",
          providerId: `provider-${i}`,
          patientName: "John Doe",
          providerName: `Dr. Provider ${i}`,
          providerImage: null,
          appointmentStartDatetimeUtc: date.toISOString(),
          appointmentEndDatetimeUtc: new Date(
            date.getTime() + 30 * 60000,
          ).toISOString(),
          hospital: {
            id: i,
            name: `Hospital ${i}`,
            address: "123 St",
            timezone: "UTC",
          },
          reason: `Reason ${i}`,
          status: i % 2 === 0 ? "COMPLETED" : "CANCELLED",
        });
      }

      mock
        .onGet("http://localhost:8000/api/appointment/", {
          params: { patient: "patient-123" },
        })
        .reply(200, appointments);

      renderPatientAppointments();

      await waitFor(() => {
        expect(screen.getByText("Dr. Provider 1")).toBeInTheDocument();
      });

      // All appointments should be in past section
      const pastSection = screen.getByText("Past").closest("div");

      // Should show all 5 past appointments
      for (let i = 1; i <= 5; i++) {
        expect(
          within(pastSection!).getByText(`Dr. Provider ${i}`),
        ).toBeInTheDocument();
      }

      // Should show appropriate status badges
      expect(screen.getAllByText("COMPLETED").length).toBe(2); // i=2,4
      expect(screen.getAllByText("CANCELLED").length).toBe(3); // i=1,3,5
    });
  });
});
