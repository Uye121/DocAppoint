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
import { ProviderHome, Login } from "../../src/pages";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Provider Medical Records Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  const renderProviderHome = () => {
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

    // Set tokens
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

  const mockConfirmedAppointments = () => {
    const now = new Date();
    const futureDate = new Date(now);
    futureDate.setHours(futureDate.getHours() + 2);

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
          reason: "Follow-up consultation",
          status: "CONFIRMED",
        },
      ]);
  };

  it("should show add record button for confirmed appointments", async () => {
    mockConfirmedAppointments();
    renderProviderHome();

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Find the Add/View Record button
    const addRecordButton = screen.getByRole("button", {
      name: /add.*record/i,
    });
    expect(addRecordButton).toBeInTheDocument();
  });

  it("should open medical record modal when clicking add record", async () => {
    mockConfirmedAppointments();

    // Mock empty medical record (no existing record)
    mock
      .onGet("http://localhost:8000/api/medical-record/", {
        params: { appointment: "appt-1" },
      })
      .reply(200, []);

    renderProviderHome();

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click add record button
    const addRecordButton = screen.getByRole("button", {
      name: /add.*record/i,
    });
    await user.click(addRecordButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText("Loading record...")).not.toBeInTheDocument();
    });

    // Click the Create Record button to enter edit mode
    const createButton = screen.getByRole("button", { name: /create record/i });
    await user.click(createButton);

    // Now the edit form should appear with empty fields
    await waitFor(() => {
      // Look for textareas by their associated labels
      const diagnosisLabel = screen.getByText("Diagnosis *");
      expect(diagnosisLabel).toBeInTheDocument();

      const notesLabel = screen.getByText("Notes *");
      expect(notesLabel).toBeInTheDocument();

      const prescriptionsLabel = screen.getByText("Prescriptions *");
      expect(prescriptionsLabel).toBeInTheDocument();
    });

    // Find the textareas by their IDs or roles
    const diagnosisTextarea = screen.getByLabelText("Diagnosis *");
    const notesTextarea = screen.getByLabelText("Notes *");
    const prescriptionsTextarea = screen.getByLabelText("Prescriptions *");

    expect(diagnosisTextarea).toBeInTheDocument();
    expect(notesTextarea).toBeInTheDocument();
    expect(prescriptionsTextarea).toBeInTheDocument();

    // Should have Save button (now showing "Create Record" since we're creating)
    const saveButton = screen.getByRole("button", { name: /create record/i });
    expect(saveButton).toBeInTheDocument();

    // Button should be disabled until fields are filled
    expect(saveButton).toBeDisabled();

    // Fill in the fields
    await user.type(diagnosisTextarea, "Test diagnosis");
    await user.type(notesTextarea, "Test notes");
    await user.type(prescriptionsTextarea, "Test prescriptions");

    // Button should now be enabled
    expect(saveButton).not.toBeDisabled();
  });

  it("should create a new medical record", async () => {
    mockConfirmedAppointments();

    // Mock empty medical record
    mock
      .onGet("http://localhost:8000/api/medical-record/", {
        params: { appointment: "appt-1" },
      })
      .reply(200, []);

    mock.onPost("http://localhost:8000/api/medical-record/").reply(201, {
      id: 1,
      patientId: "patient-123",
      providerId: "provider-123",
      hospitalId: 1,
      appointmentId: "appt-1",
      diagnosis: "Patient shows improvement",
      notes: "Follow-up visit. Blood pressure normal.",
      prescriptions: "Continue current medication",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });

    renderProviderHome();

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    const addRecordButton = screen.getByRole("button", {
      name: /add.*record/i,
    });
    await user.click(addRecordButton);

    // Wait for modal
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.queryByText("Loading record...")).not.toBeInTheDocument();
    });

    // Should show "No medical record yet" message
    expect(screen.getByText(/no medical record yet/i)).toBeInTheDocument();

    // Click the Create Record button to enter edit mode
    const createButton = screen.getByRole("button", { name: /create record/i });
    await user.click(createButton);

    // Now the edit form should appear
    await waitFor(() => {
      // Look for textareas by their associated labels (with asterisks)
      expect(screen.getByText("Diagnosis *")).toBeInTheDocument();
      expect(screen.getByText("Notes *")).toBeInTheDocument();
      expect(screen.getByText("Prescriptions *")).toBeInTheDocument();
    });

    // Fill in the form
    const diagnosisInput = screen.getByLabelText(/diagnosis/i);
    const notesInput = screen.getByLabelText(/notes/i);
    const prescriptionsInput = screen.getByLabelText(/prescriptions/i);

    await user.type(diagnosisInput, "Patient shows improvement");
    await user.type(notesInput, "Follow-up visit. Blood pressure normal.");
    await user.type(prescriptionsInput, "Continue current medication");

    // Save button should be enabled
    const saveButton = screen.getByRole("button", { name: /create record/i });
    expect(saveButton).not.toBeDisabled();

    await user.click(saveButton);

    // Verify API was called
    await waitFor(() => {
      expect(mock.history.post.length).toBe(1);
      const requestData = JSON.parse(mock.history.post[0].data);
      expect(requestData).toMatchObject({
        patientId: "patient-123",
        appointmentId: "appt-1",
        diagnosis: "Patient shows improvement",
        notes: "Follow-up visit. Blood pressure normal.",
        prescriptions: "Continue current medication",
      });
    });

    await waitFor(() => {
      expect(
        screen.getByText(/record successfully created/i),
      ).toBeInTheDocument();
    });

    await waitFor(
      () => {
        expect(screen.queryByTestId("modal-backdrop")).not.toBeInTheDocument();
      },
      { timeout: 1500 },
    );
  });

  it("should edit an existing medical record", async () => {
    mockConfirmedAppointments();

    // Mock existing medical record with the correct structure
    mock
      .onGet("http://localhost:8000/api/medical-record/", {
        params: { appointment: "appt-1" },
      })
      .reply(200, [
        {
          id: 1,
          patientDetails: {
            id: "patient-123",
            fullName: "John Doe",
            dateOfBirth: "1990-01-01",
            bloodType: "O+",
          },
          providerDetails: {
            id: "provider-123",
            fullName: "Dr. John Smith",
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
            reason: "Follow-up consultation",
            status: "COMPLETED",
          },
          diagnosis: "Previous diagnosis",
          notes: "Previous notes",
          prescriptions: "Previous prescriptions",
          createdAt: "2024-01-01T10:00:00Z",
          updatedAt: "2024-01-01T10:00:00Z",
          createdByName: "Dr. John Smith",
          updatedByName: "Dr. John Smith",
          isRemoved: false,
          removedAt: null,
        },
      ]);

    // Mock successful update
    mock.onPatch("http://localhost:8000/api/medical-record/1/").reply(200, {
      id: 1,
      diagnosis: "Updated diagnosis",
      notes: "Updated notes",
      prescriptions: "Updated prescriptions",
    });

    renderProviderHome();

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    const addRecordButton = screen.getByRole("button", {
      name: /add.*record/i,
    });
    await user.click(addRecordButton);

    // Wait for modal to appear and data to load
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    // Wait for the form fields to be populated with existing data
    const diagnosisField = await screen.findAllByText(/diagnosis/);
    expect(diagnosisField.length).toBeGreaterThan(0);

    const notesField = await screen.findAllByText(/notes/);
    expect(notesField.length).toBeGreaterThan(0);

    const prescriptionsField = await screen.findAllByText(/diagnosis/);
    expect(prescriptionsField.length).toBeGreaterThan(0);

    // Click the Edit Record button to enter edit mode
    const editButton = screen.getByRole("button", { name: /edit record/i });
    await user.click(editButton);

    // Edit the fields
    const diagnosisInput = screen.getByLabelText(/diagnosis/i);
    const notesInput = screen.getByLabelText(/notes/i);
    const prescriptionsInput = screen.getByLabelText(/prescriptions/i);

    await user.clear(diagnosisInput);
    await user.type(diagnosisInput, "Updated diagnosis");

    await user.clear(notesInput);
    await user.type(notesInput, "Updated notes");

    await user.clear(prescriptionsInput);
    await user.type(prescriptionsInput, "Updated prescriptions");

    // Save changes
    const saveButton = screen.getByRole("button", { name: /update record/i });
    expect(saveButton).not.toBeDisabled();
    await user.click(saveButton);

    // Verify API was called with correct data
    await waitFor(() => {
      expect(mock.history.patch.length).toBe(1);
      const requestData = JSON.parse(mock.history.patch[0].data);
      expect(requestData).toMatchObject({
        diagnosis: "Updated diagnosis",
        notes: "Updated notes",
        prescriptions: "Updated prescriptions",
      });
    });

    // Modal should close
    await waitFor(
      () => {
        expect(screen.queryByTestId("modal-backdrop")).not.toBeInTheDocument();
      },
      { timeout: 1500 },
    );
  });

  it("should validate required fields before saving", async () => {
    mockConfirmedAppointments();

    mock
      .onGet("http://localhost:8000/api/medical-record/", {
        params: { appointment: "appt-1" },
      })
      .reply(200, []);

    renderProviderHome();

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click add record button
    const addRecordButton = screen.getByRole("button", {
      name: /add.*record/i,
    });
    await user.click(addRecordButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    // Click the Create Record button to enter edit mode
    const createRecordButton = screen.getByRole("button", {
      name: /create record/i,
    });
    await user.click(createRecordButton);

    // Wait for edit mode
    await waitFor(() => {
      expect(screen.getByLabelText(/diagnosis/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/prescriptions/i)).toBeInTheDocument();
    });

    // In edit mode, the save button should say "Create Record"
    const saveButton = screen.getByRole("button", { name: /create record/i });

    // Save button should be disabled initially (all fields empty)
    expect(saveButton).toBeDisabled();

    // Fill only one field
    const diagnosisInput = screen.getByLabelText(/diagnosis/i);
    await user.type(diagnosisInput, "Test diagnosis");

    // Save button should still be disabled (notes and prescriptions required)
    expect(saveButton).toBeDisabled();

    // Fill all fields
    const notesInput = screen.getByLabelText(/notes/i);
    const prescriptionsInput = screen.getByLabelText(/prescriptions/i);

    await user.type(notesInput, "Test notes");
    await user.type(prescriptionsInput, "Test prescriptions");

    // Save button should now be enabled
    expect(saveButton).not.toBeDisabled();
  });

  it("should handle API errors when saving record", async () => {
    mockConfirmedAppointments();

    mock
      .onGet("http://localhost:8000/api/medical-record/", {
        params: { appointment: "appt-1" },
      })
      .reply(200, []);

    // Mock failed creation
    mock.onPost("http://localhost:8000/api/medical-record/").reply(500, {
      detail: "Server error",
    });

    renderProviderHome();

    // Wait for appointments to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click add record button
    const addRecordButton = screen.getByRole("button", {
      name: /add.*record/i,
    });
    await user.click(addRecordButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId("modal-backdrop")).toBeInTheDocument();
    });

    // Click the Create Record button to enter edit mode
    const createRecordButton = screen.getByRole("button", {
      name: /create record/i,
    });
    await user.click(createRecordButton);

    // Wait for edit mode, input field should appear
    await waitFor(() => {
      expect(screen.getByLabelText(/diagnosis/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/prescriptions/i)).toBeInTheDocument();
    });

    // Fill all fields
    const diagnosisInput = screen.getByLabelText(/diagnosis/i);
    const notesInput = screen.getByLabelText(/notes/i);
    const prescriptionsInput = screen.getByLabelText(/prescriptions/i);

    await user.type(diagnosisInput, "Test diagnosis");
    await user.type(notesInput, "Test notes");
    await user.type(prescriptionsInput, "Test prescriptions");

    const saveButton = screen.getByRole("button", { name: /create record/i });
    expect(saveButton).not.toBeDisabled();
    await user.click(saveButton);

    // Wait for error message
    await waitFor(() => {
      // Look for red text error message in the modal
      const errorElement = screen.queryByText(/server error|failed|error/i);
      expect(errorElement).toBeInTheDocument();
    });

    // Modal should still be open with entered data
    expect(screen.getByDisplayValue("Test diagnosis")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test notes")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test prescriptions")).toBeInTheDocument();

    // The save button should still be present and enabled
    expect(
      screen.getByRole("button", { name: /create record/i }),
    ).not.toBeDisabled();
  });
});
