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
import { UserAppointment, Login, Home } from "../../src/pages";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Patient Medical Records Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
    vi.clearAllMocks();

    process.env.TZ = "UTC";
  });

  const renderAppointmentsPage = (
    initialPath = "/my-appointments",
    userMock?: () => [number, unknown],
  ) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Mock authenticated user
    if (userMock) {
      mock.onGet("http://localhost:8000/api/users/me").reply(userMock);
    } else {
      mock.onGet("http://localhost:8000/api/users/me").reply(200, {
        id: "patient-123",
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

    // Set tokens
    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<div>Home Page</div>} />
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
                  <Route path="/patient-home" element={<Home />} />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  const mockAppointmentsWithRecords = () => {
    const now = new Date();
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
          reason: "Annual checkup",
          status: "COMPLETED",
        },
        {
          id: "appt-2",
          patientId: "patient-123",
          providerId: "provider-2",
          patientName: "John Doe",
          providerName: "Dr. Michael Chen",
          providerImage: null,
          appointmentStartDatetimeUtc: pastDate.toISOString(),
          appointmentEndDatetimeUtc: new Date(
            pastDate.getTime() + 30 * 60000,
          ).toISOString(),
          hospital: {
            id: 2,
            name: "Memorial Hospital",
            address: "456 Oak Ave",
            timezone: "America/New_York",
          },
          reason: "Follow-up consultation",
          status: "COMPLETED",
        },
      ]);
  };

  const mockMedicalRecord = (
    appointmentId: string,
    recordMock?: () => [number, unknown],
  ) => {
    if (recordMock) {
      mock
        .onGet(`http://localhost:8000/api/medical-record/`, {
          params: { appointment: appointmentId },
        })
        .reply(recordMock);
    } else {
      mock
        .onGet(`http://localhost:8000/api/medical-record/`, {
          params: { appointment: appointmentId },
        })
        .reply(200, [
          {
            id: 1,
            patientDetails: {
              id: "patient-123",
              fullName: "John Doe",
              dateOfBirth: "1990-01-01",
              bloodType: "O+",
              allergies: "Pollen, Peanuts",
              chronicConditions: "Asthma",
              currentMedications: "Inhaler",
            },
            providerDetails: {
              id: "provider-1",
              fullName: "Dr. Sarah Johnson",
              specialityName: "Cardiology",
              licenseNumber: "LIC12345",
            },
            hospitalDetails: {
              id: 1,
              name: "City General Hospital",
              phoneNumber: "555-123-4567",
              timezone: "America/New_York",
            },
            appointmentDetails: {
              startDatetimeUtc: "2024-01-15T09:00:00Z",
              endDatetimeUtc: "2024-01-15T09:30:00Z",
              reason: "Annual checkup",
              status: "COMPLETED",
            },
            diagnosis:
              "Patient shows mild hypertension. Continue current medication.",
            notes:
              "Blood pressure readings slightly elevated. Recommended lifestyle changes including reduced sodium intake and regular exercise. Follow up in 3 months.",
            prescriptions: "Lisinopril 10mg daily",
            createdAt: "2024-01-15T10:00:00Z",
            updatedAt: "2024-01-15T10:00:00Z",
            createdByName: "Dr. Sarah Johnson",
            updatedByName: "Dr. Sarah Johnson",
            isRemoved: false,
            removedAt: null,
          },
        ]);
    }
  };

  it("should show view records button for completed appointments", async () => {
    mockAppointmentsWithRecords();
    renderAppointmentsPage("/my-appointments");

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
      expect(screen.getByText("Dr. Michael Chen")).toBeInTheDocument();
    });

    // Both appointments should have "COMPLETED" status
    const completedBadges = screen.getAllByText("COMPLETED");
    expect(completedBadges).toHaveLength(2);

    // There should be no Cancel buttons for completed appointments
    const cancelButtons = screen.queryAllByRole("button", { name: /cancel/i });
    expect(cancelButtons).toHaveLength(0);
  });

  it("should open medical record modal when clicking on completed appointment", async () => {
    mockAppointmentsWithRecords();
    mockMedicalRecord("appt-1");

    renderAppointmentsPage("/my-appointments");

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
    });

    const appointmentCard = screen
      .getByText("Dr. Sarah Johnson")
      .closest("article");
    expect(appointmentCard).toBeInTheDocument();

    const viewRecordButton = within(appointmentCard!).getByText("View Record");
    await user.click(viewRecordButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    // The modal title should contain the patient name
    const modalTitle = screen.getByTestId("modal-title");
    expect(modalTitle).toHaveTextContent(/John Doe/i);

    // Look for provider name in the appointment details section
    const doctorElement = await screen.findAllByText(/Dr. Sarah Johnson/i);
    expect(doctorElement.length).toBeGreaterThan(0);

    // Look for hospital name
    expect(screen.getByText(/City General Hospital/i)).toBeInTheDocument();

    // Look for diagnosis in the medical record section
    expect(screen.getByText(/mild hypertension/i)).toBeInTheDocument();

    // Look for prescriptions
    expect(screen.getByText(/Lisinopril/i)).toBeInTheDocument();

    // Close modal
    const closeButton = screen.getByRole("button", { name: /✕|close/i });
    await user.click(closeButton);

    // Modal should disappear
    await waitFor(() => {
      expect(screen.queryByTestId("modal-backdrop")).not.toBeInTheDocument();
    });
  });

  it('should show "No medical record" for appointments without records', async () => {
    mockAppointmentsWithRecords();
    mockMedicalRecord("appt-1", () => [200, []]);
    renderAppointmentsPage("/my-appointments");

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
    });

    // Find the View Record button and click it
    const appointmentCard = screen
      .getByText("Dr. Sarah Johnson")
      .closest("article");
    expect(appointmentCard).toBeInTheDocument();

    const viewRecordButton = within(appointmentCard!).getByText("View Record");
    await user.click(viewRecordButton);

    // Wait for modal to appear
    await waitFor(
      () => {
        expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText("Loading record...")).not.toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    // Should show "No medical record yet" message and Create Record button
    expect(screen.getByText(/no medical record yet/i)).toBeInTheDocument();

    // Should show the Create Record button
    const createButton = screen.getByRole("button", { name: /create record/i });
    expect(createButton).toBeInTheDocument();

    // Should not show medical record details
    expect(screen.queryByText(/diagnosis/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/prescriptions/i)).not.toBeInTheDocument();

    // Should not show edit button
    expect(
      screen.queryByRole("button", { name: /edit record/i }),
    ).not.toBeInTheDocument();

    // Verify modal title shows patient name
    const modalTitle = screen.getByTestId("modal-title");
    expect(modalTitle).toHaveTextContent(/John Doe/i);

    // Close modal
    const closeButton = screen.getByRole("button", { name: /✕|close/i });
    await user.click(closeButton);

    // Modal should disappear
    await waitFor(() => {
      expect(screen.queryByTestId("modal-backdrop")).not.toBeInTheDocument();
    });
  });

  it("should display formatted dates correctly", async () => {
    mockAppointmentsWithRecords();
    mockMedicalRecord("appt-1");
    renderAppointmentsPage("/my-appointments");

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("Dr. Sarah Johnson")).toBeInTheDocument();
    });

    // Click on View Record button
    const appointmentCard = screen
      .getByText("Dr. Sarah Johnson")
      .closest("article");
    expect(appointmentCard).toBeInTheDocument();

    const viewRecordButton = within(appointmentCard!).getByText("View Record");
    await user.click(viewRecordButton);

    // Wait for modal to appear and loading to complete
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.queryByText("Loading record...")).not.toBeInTheDocument();
    });

    // Find the Appointment Details section
    const appointmentSection = screen
      .getByText(/Appointment Details/i)
      .closest("div");
    expect(appointmentSection).toBeInTheDocument();

    // Look for the formatted date in the appointment details
    expect(appointmentSection).toHaveTextContent(/2024/);
    expect(appointmentSection).toHaveTextContent(/Jan/);
    expect(appointmentSection).toHaveTextContent(/15/);
    expect(appointmentSection).toHaveTextContent(/9:00 AM/);
    expect(appointmentSection).toHaveTextContent(/9:30 AM/);

    // Check for created date in Record Information section
    const recordInfoSection = screen
      .getByText(/Record Information/i)
      .closest("div");
    expect(recordInfoSection).toBeInTheDocument();

    // Verify they appear in the correct context
    const createdText = within(recordInfoSection!).getByText(/Created/i);
    expect(createdText).toBeInTheDocument();

    // The created date should be near the "Created" text
    const createdRow = createdText.closest("div");
    expect(createdRow).toHaveTextContent(/Created/i);
    expect(createdRow).toHaveTextContent(/Jan 15, 2024, 10:00 AM/i);

    const updatedText = within(recordInfoSection!).getByText(/Last Updated/i);
    expect(updatedText).toBeInTheDocument();

    // The updated date should be near the "Last Updated" text
    const updatedRow = updatedText.closest("div");
    expect(updatedRow).toHaveTextContent(/Last Updated/i);
    expect(updatedRow).toHaveTextContent(/Jan 15, 2024, 10:00 AM/i);
  });

  it("should not show medical records for upcoming appointments", async () => {
    const now = new Date();
    const futureDate = new Date(now);
    futureDate.setDate(futureDate.getDate() + 7);

    mock
      .onGet("http://localhost:8000/api/appointment/", {
        params: { patient: "patient-123" },
      })
      .reply(200, [
        {
          id: "appt-3",
          patientId: "patient-123",
          providerId: "provider-3",
          patientName: "John Doe",
          providerName: "Dr. Emily Brown",
          providerImage: null,
          appointmentStartDatetimeUtc: futureDate.toISOString(),
          appointmentEndDatetimeUtc: new Date(
            futureDate.getTime() + 30 * 60000,
          ).toISOString(),
          hospital: {
            id: 3,
            name: "University Medical Center",
            address: "789 College Blvd",
            timezone: "America/New_York",
          },
          reason: "Consultation",
          status: "CONFIRMED",
        },
      ]);

    renderAppointmentsPage("/my-appointments");

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("Dr. Emily Brown")).toBeInTheDocument();
    });

    // Status should be CONFIRMED, not COMPLETED
    expect(screen.getByText("CONFIRMED")).toBeInTheDocument();

    // Verify that there is NO "View Record" button for this appointment
    const appointmentCard = screen
      .getByText("Dr. Emily Brown")
      .closest("article");
    expect(appointmentCard).toBeInTheDocument();

    // Check that View Record button does NOT exist
    const viewRecordButton = within(appointmentCard!).queryByText(
      "View Record",
    );
    expect(viewRecordButton).not.toBeInTheDocument();

    const cancelButton = within(appointmentCard!).queryByText("Cancel");
    if (cancelButton) {
      expect(cancelButton).toBeInTheDocument();
    }

    await user.click(appointmentCard!);

    // Verify modal does not appear
    await waitFor(
      () => {
        expect(screen.queryByTestId("modal-backdrop")).not.toBeInTheDocument();
      },
      { timeout: 200 },
    );
  });
});
