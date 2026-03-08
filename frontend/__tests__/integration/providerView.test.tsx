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
import { ProviderHome, Login } from "../../src/pages/";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Provider Dashboard Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
    process.env.TZ = "UTC";
    vi.setSystemTime(new Date("2024-01-16T12:00:00Z"));
  });

  const renderProviderDashboard = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Mock authenticated provider
    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: "provider-123",
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

  const mockAppointments = (
    requestedCount = 1,
    confirmedCount = 1,
    completedCount = 1,
    includeTodayAppointment = true,
  ) => {
    const fixedDate = new Date("2024-01-16T12:00:00Z");
    const todayDate = new Date(fixedDate);
    const futureDate = new Date(fixedDate);
    futureDate.setDate(futureDate.getDate() + 7);
    const pastDate = new Date(fixedDate);
    pastDate.setDate(pastDate.getDate() - 7);

    const appointments = [];

    // Add requested appointments
    for (let i = 0; i < requestedCount; i += 1) {
      appointments.push({
        id: `requested-${i}`,
        patientId: `patient-${i}`,
        providerId: "provider-123",
        patientName: `John Doe ${i}`,
        providerName: "Dr. John Smith",
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
        reason: "Initial consultation",
        status: "REQUESTED",
      });
    }

    // Add confirmed appointments
    for (let i = 0; i < confirmedCount; i += 1) {
      appointments.push({
        id: `confirmed-${i}`,
        patientId: `patient-${i}`,
        providerId: "provider-123",
        patientName: `Jane Smith ${i}`,
        providerName: "Dr. John Smith",
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
        reason: "Follow-up visit",
        status: "CONFIRMED",
      });
    }

    // Add completed appointments
    for (let i = 0; i < completedCount; i += 1) {
      appointments.push({
        id: `completed-${i}`,
        patientId: `patient-${i}`,
        providerId: "provider-123",
        patientName: `Bob Johnson ${i}`,
        providerName: "Dr. John Smith",
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
        reason: "Annual checkup",
        status: "COMPLETED",
      });
    }

    // Add today's confirmed appointment (optional)
    if (includeTodayAppointment) {
      appointments.push({
        id: "today-confirmed",
        patientId: "patient-today",
        providerId: "provider-123",
        patientName: "Today Patient",
        providerName: "Dr. John Smith",
        providerImage: null,
        appointmentStartDatetimeUtc: todayDate.toISOString(),
        appointmentEndDatetimeUtc: new Date(
          todayDate.getTime() + 30 * 60000,
        ).toISOString(),
        hospital: {
          id: 1,
          name: "City General Hospital",
          address: "123 Main St",
          timezone: "America/New_York",
        },
        reason: "Today appointment",
        status: "CONFIRMED",
      });
    }

    mock
      .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
      .reply(200, appointments);
  };

  describe("Dashboard Layout", () => {
    it("should display all appointment status sections", async () => {
      mockAppointments(0, 0, 0);
      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("REQUESTED Appointments")).toBeInTheDocument();
        expect(screen.getByText("CONFIRMED Appointments")).toBeInTheDocument();
        expect(
          screen.getByText("RESCHEDULED Appointments"),
        ).toBeInTheDocument();
        expect(screen.getByText("COMPLETED Appointments")).toBeInTheDocument();
      });
    });

    it("should display today's appointment count", async () => {
      mockAppointments(0, 1, 0);
      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Today")).toBeInTheDocument();
        expect(screen.getByText(/1 appointments?/i)).toBeInTheDocument();
      });
    });

    it("should show correct count for today's appointments", async () => {
      mockAppointments(0, 2, 0); // 2 confirmed, one of which is today
      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Today")).toBeInTheDocument();
        expect(screen.getByText(/1 appointments?/i)).toBeInTheDocument();
      });
    });
  });

  describe("Requested Appointments", () => {
    it("should display requested appointments with Confirm and Reject buttons", async () => {
      mockAppointments(2, 0, 0);
      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("John Doe 0")).toBeInTheDocument();
        expect(screen.getByText("John Doe 1")).toBeInTheDocument();
      });

      const requestedSection = screen
        .getByText("REQUESTED Appointments")
        .closest("section");
      expect(requestedSection).toBeInTheDocument();

      const confirmButtons = within(requestedSection!).getAllByRole("button", {
        name: /confirm/i,
      });
      const rejectButtons = within(requestedSection!).getAllByRole("button", {
        name: /reject/i,
      });

      expect(confirmButtons).toHaveLength(2);
      expect(rejectButtons).toHaveLength(2);
    });

    it("should show empty state when no requested appointments", async () => {
      mockAppointments(0, 1, 1);
      renderProviderDashboard();

      await waitFor(() => {
        const requestedSection = screen
          .getByText("REQUESTED Appointments")
          .closest("section");
        expect(
          within(requestedSection!).getByText(/no requested appointments/i),
        ).toBeInTheDocument();
      });
    });

    it("should confirm a requested appointment", async () => {
      let appointmentStatus = "REQUESTED";

      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(() => {
          return [
            200,
            [
              {
                id: "requested-0",
                patientId: "patient-0",
                providerId: "provider-123",
                patientName: "John Doe",
                providerName: "Dr. John Smith",
                providerImage: null,
                appointmentStartDatetimeUtc: new Date(
                  "2024-01-23T12:00:00Z",
                ).toISOString(),
                appointmentEndDatetimeUtc: new Date(
                  "2024-01-23T12:30:00Z",
                ).toISOString(),
                hospital: {
                  id: 1,
                  name: "City General Hospital",
                  address: "123 Main St",
                  timezone: "America/New_York",
                },
                reason: "Initial consultation",
                status: appointmentStatus,
              },
            ],
          ];
        });

      mock
        .onPost("http://localhost:8000/api/appointment/requested-0/set-status/")
        .reply(() => {
          appointmentStatus = "CONFIRMED";
          return [200, { detail: "Appointment confirmed successfully" }];
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

      expect(
        screen.queryByRole("button", { name: /confirm/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /reject/i }),
      ).not.toBeInTheDocument();
    });

    it("should reject (cancel) a requested appointment", async () => {
      let appointmentStatus = "REQUESTED";

      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(() => {
          return [
            200,
            [
              {
                id: "requested-0",
                patientId: "patient-0",
                providerId: "provider-123",
                patientName: "John Doe",
                providerName: "Dr. John Smith",
                providerImage: null,
                appointmentStartDatetimeUtc: new Date(
                  "2024-01-23T12:00:00Z",
                ).toISOString(),
                appointmentEndDatetimeUtc: new Date(
                  "2024-01-23T12:30:00Z",
                ).toISOString(),
                hospital: {
                  id: 1,
                  name: "City General Hospital",
                  address: "123 Main St",
                  timezone: "America/New_York",
                },
                reason: "Initial consultation",
                status: appointmentStatus,
              },
            ],
          ];
        });

      mock
        .onPost("http://localhost:8000/api/appointment/requested-0/set-status/")
        .reply(() => {
          appointmentStatus = "CANCELLED";
          return [200, { detail: "Appointment cancelled successfully" }];
        });

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("REQUESTED")).toBeInTheDocument();
      });

      const rejectButton = screen.getByRole("button", { name: /reject/i });
      await user.click(rejectButton);

      await waitFor(() => {
        const requestedSection = screen
          .getByText("REQUESTED Appointments")
          .closest("section");
        expect(
          within(requestedSection!).queryByText("John Doe"),
        ).not.toBeInTheDocument();
      });
    });

    it("should handle API error when confirming appointment", async () => {
      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(200, [
          {
            id: "requested-0",
            patientId: "patient-0",
            providerId: "provider-123",
            patientName: "John Doe",
            providerName: "Dr. John Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: new Date(
              "2024-01-23T12:00:00Z",
            ).toISOString(),
            appointmentEndDatetimeUtc: new Date(
              "2024-01-23T12:30:00Z",
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Initial consultation",
            status: "REQUESTED",
          },
        ]);

      mock
        .onPost("http://localhost:8000/api/appointment/requested-0/set-status/")
        .reply(500, {
          detail: "Server error",
        });

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("REQUESTED")).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole("button", { name: /confirm/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining("Server error"),
        );
      });

      expect(screen.getByText("REQUESTED")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /confirm/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reject/i }),
      ).toBeInTheDocument();
    });
  });

  describe("Confirmed Appointments", () => {
    it("should display confirmed appointments with Add/View Record button", async () => {
      mockAppointments(0, 2, 0);
      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Jane Smith 0")).toBeInTheDocument();
        expect(screen.getByText("Jane Smith 1")).toBeInTheDocument();
      });

      const confirmedSection = screen
        .getByText("CONFIRMED Appointments")
        .closest("section");
      expect(confirmedSection).toBeInTheDocument();

      const recordButtons = within(confirmedSection!).getAllByRole("button", {
        name: /add.*record/i,
      });
      expect(recordButtons).toHaveLength(3);
    });

    it("should show empty state when no confirmed appointments", async () => {
      mockAppointments(1, 0, 1, false); // Add false to exclude today appointment
      renderProviderDashboard();

      await waitFor(() => {
        const confirmedSection = screen
          .getByText("CONFIRMED Appointments")
          .closest("section");
        expect(
          within(confirmedSection!).getByText(/no confirmed appointments/i),
        ).toBeInTheDocument();
      });
    });

    it("should open medical record modal when clicking Add/View Record", async () => {
      mockAppointments(0, 1, 0, true);

      mock
        .onGet("http://localhost:8000/api/medical-record/")
        .reply((config) => {
          const url = new URL(config.url!, "http://localhost:8000");
          const appointmentId = url.searchParams.get("appointment");

          if (appointmentId === "confirmed-0") {
            return [200, []];
          }
          return [200, []];
        });

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Jane Smith 0")).toBeInTheDocument();
      });

      const appointmentContainers = screen
        .getAllByText("Jane Smith 0")
        .map((el) => el.closest(".flex.flex-col.sm\\:flex-row"));

      // Get the first matching container
      const appointmentCard = appointmentContainers[0];
      expect(appointmentCard).toBeInTheDocument();

      const recordButton = within(appointmentCard!).getByRole("button", {
        name: /add.*record/i,
      });
      await user.click(recordButton);

      await waitFor(() => {
        expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
      });

      const modalTitle = screen.getByTestId("modal-title");
      expect(modalTitle).toHaveTextContent(/medical record/i);
    });
  });

  describe("Completed Appointments", () => {
    it("should display completed appointments with Add/View Record button", async () => {
      mockAppointments(0, 0, 2);
      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Bob Johnson 0")).toBeInTheDocument();
        expect(screen.getByText("Bob Johnson 1")).toBeInTheDocument();
      });

      const completedSection = screen
        .getByText("COMPLETED Appointments")
        .closest("section");
      expect(completedSection).toBeInTheDocument();

      const recordButtons = within(completedSection!).getAllByRole("button", {
        name: /add.*record/i,
      });
      expect(recordButtons).toHaveLength(2);
    });

    it("should show empty state when no completed appointments", async () => {
      mockAppointments(1, 1, 0);
      renderProviderDashboard();

      await waitFor(() => {
        const completedSection = screen
          .getByText("COMPLETED Appointments")
          .closest("section");
        expect(
          within(completedSection!).getByText(/no completed appointments/i),
        ).toBeInTheDocument();
      });
    });

    it("should open medical record modal for completed appointments", async () => {
      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(200, [
          {
            id: "completed-0",
            patientId: "patient-0",
            providerId: "provider-123",
            patientName: "Bob Johnson 0",
            providerName: "Dr. John Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: "2024-01-09T12:00:00.000Z",
            appointmentEndDatetimeUtc: "2024-01-09T12:30:00.000Z",
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Annual checkup",
            status: "COMPLETED",
          },
        ]);

      mock
        .onGet("http://localhost:8000/api/medical-record/")
        .reply((config) => {
          // Check if the appointment param is in the request
          if (config.params?.appointment === "completed-0") {
            return [
              200,
              [
                {
                  id: 1,
                  patientDetails: {
                    fullName: "Bob Johnson 0",
                  },
                  providerDetails: {
                    fullName: "Dr. John Smith",
                  },
                  hospitalDetails: {
                    name: "City General Hospital",
                  },
                  appointmentDetails: {
                    reason: "Annual checkup",
                    status: "COMPLETED",
                  },
                  diagnosis: "Previous diagnosis",
                  notes: "Previous notes",
                  prescriptions: "Previous prescriptions",
                  createdAt: "2024-01-01T10:00:00Z",
                  updatedAt: "2024-01-01T10:00:00Z",
                  createdByName: "Dr. John Smith",
                  updatedByName: "Dr. John Smith",
                },
              ],
            ];
          }

          console.log("No matching appointment param, returning empty array");
          return [200, []];
        });

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Bob Johnson 0")).toBeInTheDocument();
      });

      // Find the specific appointment container for Bob Johnson 0
      const appointmentContainers = screen
        .getAllByText("Bob Johnson 0")
        .map((el) => el.closest(".flex.flex-col.sm\\:flex-row"));

      const appointmentCard = appointmentContainers[0];
      expect(appointmentCard).toBeInTheDocument();

      const recordButton = within(appointmentCard!).getByRole("button", {
        name: /add.*record/i,
      });
      await user.click(recordButton);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
      });

      // Wait for the medical record data to load (should show diagnosis, not empty state)
      await waitFor(() => {
        expect(
          screen.queryByText(/no medical record yet/i),
        ).not.toBeInTheDocument();
      });

      // Now check for the diagnosis
      expect(screen.getByText(/previous diagnosis/i)).toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    it("should display error message when appointments fail to load", async () => {
      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(500, {
          detail: "Failed to load appointments",
        });

      renderProviderDashboard();

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining("Failed to load"),
        );
      });
    });

    it("should handle network errors gracefully", async () => {
      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .networkError();

      renderProviderDashboard();

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining("Failed to load appointments"),
        );
      });
    });
  });

  describe("Rescheduled Appointments", () => {
    it("should display rescheduled appointments section", async () => {
      const fixedDate = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(fixedDate);
      futureDate.setDate(futureDate.getDate() + 7);

      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(200, [
          {
            id: "rescheduled-0",
            patientId: "patient-0",
            providerId: "provider-123",
            patientName: "Rescheduled Patient",
            providerName: "Dr. John Smith",
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
            reason: "Rescheduled appointment",
            status: "RESCHEDULED",
          },
        ]);

      renderProviderDashboard();

      await waitFor(() => {
        expect(
          screen.getByText("RESCHEDULED Appointments"),
        ).toBeInTheDocument();
        expect(screen.getByText("Rescheduled Patient")).toBeInTheDocument();
        expect(screen.getByText("RESCHEDULED")).toBeInTheDocument();
      });
    });

    it("should show empty state for rescheduled appointments", async () => {
      mockAppointments(1, 1, 1); // No rescheduled
      renderProviderDashboard();

      await waitFor(() => {
        const rescheduledSection = screen
          .getByText("RESCHEDULED Appointments")
          .closest("section");
        expect(
          within(rescheduledSection!).getByText(/no rescheduled appointments/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Dashboard Statistics", () => {
    it("should calculate today's appointments correctly", async () => {
      const fixedDate = new Date("2024-01-16T12:00:00Z");

      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(200, [
          {
            id: "today-1",
            patientId: "patient-1",
            providerId: "provider-123",
            patientName: "Today Patient 1",
            providerName: "Dr. John Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: fixedDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              fixedDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Today appointment 1",
            status: "CONFIRMED",
          },
          {
            id: "today-2",
            patientId: "patient-2",
            providerId: "provider-123",
            patientName: "Today Patient 2",
            providerName: "Dr. John Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: fixedDate.toISOString(),
            appointmentEndDatetimeUtc: new Date(
              fixedDate.getTime() + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Today appointment 2",
            status: "CONFIRMED",
          },
          {
            id: "future",
            patientId: "patient-3",
            providerId: "provider-123",
            patientName: "Future Patient",
            providerName: "Dr. John Smith",
            providerImage: null,
            appointmentStartDatetimeUtc: new Date(
              fixedDate.getTime() + 7 * 24 * 60 * 60000,
            ).toISOString(),
            appointmentEndDatetimeUtc: new Date(
              fixedDate.getTime() + 7 * 24 * 60 * 60000 + 30 * 60000,
            ).toISOString(),
            hospital: {
              id: 1,
              name: "City General Hospital",
              address: "123 Main St",
              timezone: "America/New_York",
            },
            reason: "Future appointment",
            status: "CONFIRMED",
          },
        ]);

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Today")).toBeInTheDocument();
        expect(screen.getByText(/2 appointments?/i)).toBeInTheDocument();
      });
    });

    it("should show 0 appointments when none today", async () => {
      const fixedDate = new Date("2024-01-16T12:00:00Z");
      const futureDate = new Date(fixedDate);
      futureDate.setDate(futureDate.getDate() + 1);

      mock
        .onGet("http://localhost:8000/api/appointment/?provider=provider-123")
        .reply(200, [
          {
            id: "future",
            patientId: "patient-1",
            providerId: "provider-123",
            patientName: "Future Patient",
            providerName: "Dr. John Smith",
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
            reason: "Future appointment",
            status: "CONFIRMED",
          },
        ]);

      renderProviderDashboard();

      await waitFor(() => {
        expect(screen.getByText("Today")).toBeInTheDocument();
        expect(screen.getByText(/0 appointments?/i)).toBeInTheDocument();
      });
    });
  });
});
