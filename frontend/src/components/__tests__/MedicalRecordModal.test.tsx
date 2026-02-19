import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import MedicalRecordModal from "../MedicalRecordModal";
import * as medicalRecordApi from "../../api/medicalRecord";

const mockPatient = {
  id: "1",
  bloodType: "A",
  allergies: "pollen",
  chronicConditions: "back pain",
  currentMedications: "tylenol",
  insurance: "",
  weight: 75,
  height: 170,
  fullName: "Mark Paul",
  dateOfBirth: "",
  image: "pic.jpg",
};

const mockProvider = {
  id: "2",
  specialityName: "pulmonologist",
  licenseNumber: "abc123",
  fullName: "John Doe",
};

const mockHospital = {
  id: 9,
  name: "General Hospital",
  address: "123 Main St.",
  phoneNumber: "123-456-7890",
  timezone: "US/NewYork",
};

const mockAppointment = {
  id: "1",
  patientId: mockPatient.id,
  providerId: mockProvider.id,
  patientName: mockPatient.fullName,
  providerName: mockProvider.fullName,
  providerImage: "pic.jpg",
  appointmentStartDatetimeUtc: "2026-01-21T22:30:00Z",
  appointmentEndDatetimeUtc: "2026-01-21T23:00:00Z",
  hospital: mockHospital,
  reason: "test",
  status: "CONFIRMED",
};

const mockRecord = {
  id: 1,
  patientDetails: mockPatient,
  providerDetails: mockProvider,
  hospitalDetails: mockHospital,
  appointmentDetails: mockAppointment,
  diagnosis: "respiratory infection",
  notes: "breathing problem",
  prescriptions: "ibuprofen",
  createdAt: "2026-01-21T21:30:00Z",
  updatedAt: "2026-01-21T21:30:00Z",
  createdBy: "2",
  updatedBy: "2",
  updatedByName: "John",
  createdByName: "John",
  isRemoved: false,
  removedAt: "",
};

const mockUpdateRecord = {
  patientId: mockPatient.id,
  hospitalId: mockHospital.id,
  appointmentId: mockAppointment.id,
  diagnosis: mockRecord.diagnosis,
  notes: mockRecord.notes,
  prescriptions: mockRecord.prescriptions,
};

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(() => ({ user: mockProvider })),
}));
vi.mock("../../api/medicalRecord", () => ({
  getMedicalRecordByAppointment: vi.fn(() => [mockRecord]),
  createMedicalRecord: vi.fn(() => mockRecord),
  updateMedicalRecord: vi.fn(() => mockUpdateRecord),
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("MedicalRecordModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should not render when show is false", () => {
    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={false}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    expect(screen.queryByText(/Medical Record/i)).not.toBeInTheDocument();
  });

  it("should show loading state while fetching record", () => {
    // Mock the API to return a pending promise
    vi.mocked(
      medicalRecordApi.getMedicalRecordByAppointment,
    ).mockImplementation(() => new Promise(() => {}));

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    expect(screen.getByText(/Loading record/i)).toBeInTheDocument();
  });

  it("should display medical record data when record exists", async () => {
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      mockRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText(mockRecord.diagnosis)).toBeInTheDocument();
      expect(screen.getByText(mockRecord.notes)).toBeInTheDocument();
      expect(screen.getByText(mockRecord.prescriptions)).toBeInTheDocument();
    });

    expect(screen.getByText(mockPatient.bloodType)).toBeInTheDocument();
    expect(screen.getByText(mockPatient.allergies)).toBeInTheDocument();
    expect(screen.getByText(`${mockPatient.weight} kg`)).toBeInTheDocument();

    expect(screen.getByText("Edit Record")).toBeInTheDocument();
  });

  it("should show create record view when no record exists", async () => {
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      null,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText(/No medical record yet/i)).toBeInTheDocument();
      expect(screen.getByText("Create Record")).toBeInTheDocument();
    });
  });

  it("should not show edit button for records created by other providers", async () => {
    const otherProviderRecord = {
      ...mockRecord,
      providerDetails: { ...mockProvider, id: "other-provider" },
    };

    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      otherProviderRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.queryByText("Edit Record")).not.toBeInTheDocument();
    });
  });

  it("should switch to edit mode when Edit button is clicked", async () => {
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      mockRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Edit Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Edit Record"));

    expect(screen.getByText("Update Record")).toBeInTheDocument();
    expect(screen.getByDisplayValue(mockRecord.diagnosis)).toBeInTheDocument();
    expect(screen.getByDisplayValue(mockRecord.notes)).toBeInTheDocument();
    expect(
      screen.getByDisplayValue(mockRecord.prescriptions),
    ).toBeInTheDocument();
  });

  it("should call createMedicalRecord when creating a new record", async () => {
    const user = userEvent.setup();
    const mockCreate = vi
      .mocked(medicalRecordApi.createMedicalRecord)
      .mockResolvedValue(mockRecord);
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      null,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Create Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Create Record"));

    await user.type(screen.getByLabelText(/Diagnosis/i), "New Diagnosis");
    await user.type(screen.getByLabelText(/Notes/i), "New Notes");
    await user.type(
      screen.getByLabelText(/Prescriptions/i),
      "New Prescriptions",
    );

    fireEvent.click(screen.getByText("Create Record"));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        patientId: mockAppointment.patientId,
        hospitalId: mockAppointment.hospital.id,
        appointmentId: mockAppointment.id,
        diagnosis: "New Diagnosis",
        notes: "New Notes",
        prescriptions: "New Prescriptions",
      });
    });
  });

  it("should call updateMedicalRecord when updating an existing record", async () => {
    const user = userEvent.setup();
    const mockUpdate = vi
      .mocked(medicalRecordApi.updateMedicalRecord)
      .mockResolvedValue(mockRecord);
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      mockRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Edit Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Edit Record"));

    // Update the form
    const diagnosisInput = screen.getByDisplayValue(mockRecord.diagnosis);
    await user.clear(diagnosisInput);
    await user.type(diagnosisInput, "Updated Diagnosis");

    fireEvent.click(screen.getByText("Update Record"));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(
        mockRecord.id,
        expect.objectContaining({
          diagnosis: "Updated Diagnosis",
        }),
      );
    });
  });

  it("should disable save button when required fields are empty", async () => {
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      null,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Create Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Create Record"));

    // Save button should be disabled initially
    expect(screen.getByText("Create Record")).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Diagnosis/i), {
      target: { value: "Test" },
    });

    // Button should still be disabled
    expect(screen.getByText("Create Record")).toBeDisabled();
  });

  it("should call onClose when clicking close button", async () => {
    const mockOnClose = vi.fn();
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      mockRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={mockOnClose}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Medical Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("✕"));

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should call onClose when clicking outside the modal", async () => {
    const mockOnClose = vi.fn();
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      mockRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={mockOnClose}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Medical Record")).toBeInTheDocument();
    });

    // Click the backdrop
    fireEvent.click(screen.getByTestId("modal-backdrop"));

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should display error message when create mutation fails", async () => {
    const mockError = new Error("Failed to create");
    vi.mocked(medicalRecordApi.createMedicalRecord).mockRejectedValue(
      mockError,
    );
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      null,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Create Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Create Record"));

    // Fill form
    fireEvent.change(screen.getByLabelText(/Diagnosis/i), {
      target: { value: "Test" },
    });
    fireEvent.change(screen.getByLabelText(/Notes/i), {
      target: { value: "Test" },
    });
    fireEvent.change(screen.getByLabelText(/Prescriptions/i), {
      target: { value: "Test" },
    });

    fireEvent.click(screen.getByText("Create Record"));

    await waitFor(() => {
      expect(screen.getByText(/Error creating record/i)).toBeInTheDocument();
    });
  });

  it("should reset form when cancel is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(medicalRecordApi.getMedicalRecordByAppointment).mockResolvedValue(
      mockRecord,
    );

    render(
      <TestWrapper>
        <MedicalRecordModal
          selectedAppt={mockAppointment}
          show={true}
          onClose={() => {}}
        />
      </TestWrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Edit Record")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Edit Record"));

    const diagnosisInput = screen.getByDisplayValue(mockRecord.diagnosis);
    await user.clear(diagnosisInput);
    await user.type(diagnosisInput, "Changed Diagnosis");

    fireEvent.click(screen.getByText("Cancel"));

    // Should revert to view mode with original values
    expect(screen.queryByText("Update Record")).not.toBeInTheDocument();
    expect(screen.getByText(mockRecord.diagnosis)).toBeInTheDocument();
  });
});
