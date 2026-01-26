import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ProviderHome from "../ProviderHome";
import { useAuth } from "../../../hooks/useAuth";
import {
  getProviderAppointments,
  updateAppointmentStatus,
} from "../../api/appointment";

// Mock dependencies
vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../api/appointment", () => ({
  getProviderAppointments: vi.fn(),
  updateAppointmentStatus: vi.fn(),
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

const mockAppointments = [
  {
    id: "1",
    patientName: "John Doe",
    appointmentStartDatetimeUtc: new Date("2024-06-15T10:00:00Z").toISOString(), // Unique date
    reason: "Annual checkup",
    status: "REQUESTED",
    patient: { id: "p1", firstName: "John", lastName: "Doe" },
  },
  {
    id: "2",
    patientName: "Jane Smith",
    appointmentStartDatetimeUtc: new Date("2024-06-16T14:30:00Z").toISOString(), // Different date
    reason: "Follow-up",
    status: "CONFIRMED",
    patient: { id: "p2", firstName: "Jane", lastName: "Smith" },
  },
  {
    id: "3",
    patientName: "Bob Johnson",
    appointmentStartDatetimeUtc: new Date("2024-06-17T09:00:00Z").toISOString(), // Different date
    reason: "Consultation",
    status: "RESCHEDULED",
    patient: { id: "p3", firstName: "Bob", lastName: "Johnson" },
  },
];

describe("ProviderHome", () => {
  const mockUser = { id: "provider-123", name: "Dr. Test" };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({ user: mockUser });
    vi.mocked(getProviderAppointments).mockResolvedValue(mockAppointments);
  });

  it("shows loading spinner initially", () => {
    vi.mocked(getProviderAppointments).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    render(<ProviderHome />, { wrapper: TestWrapper });

    expect(screen.getByText(/loading appointments/i)).toBeInTheDocument();
  });

  it("renders appointments grouped by status", async () => {
    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Check section headings
    expect(screen.getByText("REQUESTED Appointments")).toBeInTheDocument();
    expect(screen.getByText("CONFIRMED Appointments")).toBeInTheDocument();
    expect(screen.getByText("RESCHEDULED Appointments")).toBeInTheDocument();

    // Check appointments appear in correct sections
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
  });

  it("shows 'No appointments' message for empty status", async () => {
    vi.mocked(getProviderAppointments).mockResolvedValue([]);

    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(
        screen.getByText(/no requested appointments/i),
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/no confirmed appointments/i)).toBeInTheDocument();
    expect(
      screen.getByText(/no rescheduled appointments/i),
    ).toBeInTheDocument();
  });

  it("confirms requested appointment", async () => {
    const user = userEvent.setup();
    vi.mocked(updateAppointmentStatus).mockResolvedValue(undefined);

    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole("button", { name: /confirm/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(vi.mocked(updateAppointmentStatus)).toHaveBeenCalledWith(
        "1",
        "CONFIRMED",
      );
    });
  });

  it("cancels requested appointment", async () => {
    const user = userEvent.setup();
    vi.mocked(updateAppointmentStatus).mockResolvedValue(undefined);

    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    const rejectButton = screen.getByRole("button", { name: /reject/i });
    await user.click(rejectButton);

    await waitFor(() => {
      expect(vi.mocked(updateAppointmentStatus)).toHaveBeenCalledWith(
        "1",
        "CANCELLED",
      );
    });
  });

  it("shows today's appointment count", async () => {
    const today = new Date();
    const todayAppointments = [
      {
        id: "1",
        patientName: "Today Patient",
        appointmentStartDatetimeUtc: today.toISOString(),
        reason: "Checkup",
        status: "CONFIRMED",
        patient: { id: "p1", firstName: "Today", lastName: "Patient" },
      },
    ];

    vi.mocked(getProviderAppointments).mockResolvedValue(todayAppointments);

    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Today" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("1 appointments")).toBeInTheDocument();
  });

  it("shows zero appointments when none today", async () => {
    const tomorrow = new Date(Date.now() + 86400000);
    const tomorrowAppointments = [
      {
        id: "1",
        patientName: "Tomorrow Patient",
        appointmentStartDatetimeUtc: tomorrow.toISOString(),
        reason: "Checkup",
        status: "CONFIRMED",
        patient: { id: "p1", firstName: "Tomorrow", lastName: "Patient" },
      },
    ];

    vi.mocked(getProviderAppointments).mockResolvedValue(tomorrowAppointments);

    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("0 appointments")).toBeInTheDocument();
    });
  });

  it("displays appointment details correctly", async () => {
    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    expect(screen.getByText("Annual checkup")).toBeInTheDocument();
    expect(screen.getByText(/jun 15, 2024/i)).toBeInTheDocument(); // Unique to John Doe

    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByText("Follow-up")).toBeInTheDocument();
    expect(screen.getByText(/jun 16, 2024/i)).toBeInTheDocument(); // Unique to Jane Smith

    expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
    expect(screen.getByText("Consultation")).toBeInTheDocument();
    expect(screen.getByText(/jun 17, 2024/i)).toBeInTheDocument(); // Unique to Bob Johnson
  });

  it("displays appointment date formatted correctly", async () => {
    const fixedDate = new Date("2024-06-15T14:30:00Z");
    const appointmentWithFixedDate = [
      {
        id: "1",
        patientName: "Fixed Date Patient",
        appointmentStartDatetimeUtc: fixedDate.toISOString(),
        reason: "Checkup",
        status: "CONFIRMED",
        patient: { id: "p1", firstName: "Fixed", lastName: "Date" },
      },
    ];

    vi.mocked(getProviderAppointments).mockResolvedValue(
      appointmentWithFixedDate,
    );

    render(<ProviderHome />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("Fixed Date Patient")).toBeInTheDocument();
    });

    // Check that date-fns formatted the date (format "PPp" = Jun 15, 2024, 2:30 PM)
    expect(screen.getByText(/jun 15, 2024/i)).toBeInTheDocument();
  });
});
