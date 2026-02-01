import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

import UserAppointment from "../UserAppointment";
import { useAuth } from "../../../hooks/useAuth";
import { getPatientAppointments } from "../../api/appointment";
import type { AppointmentListItem } from "../../types/appointment";
import type { AuthCtx } from "../../types/auth";
import { HospitalTiny } from "../../types/hospital";

vi.mock("../../../hooks/useAuth");
vi.mock("../../api/appointment", () => ({
  getPatientAppointments: vi.fn(),
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter>
    <QueryClientProvider client={createTestQueryClient()}>
      {children}
    </QueryClientProvider>
  </MemoryRouter>
);

const hospital: HospitalTiny = {
  id: 1,
  name: "General Hospital",
  address: "123 Main St",
  timezone: "utc",
};

const baseAppt = (): AppointmentListItem => ({
  id: "1",
  patientId: "1",
  providerId: "2",
  patientName: "Joe",
  providerName: "Dr. Smith",
  providerImage: null,
  appointmentStartDatetimeUtc: "2026-02-01T10:00:00Z", // future
  appointmentEndDatetimeUtc: "2026-02-01T10:30:00Z",
  hospital: hospital,
  reason: "Check-up",
  status: "CONFIRMED" as const,
});

const mockAppts = (overrides: Partial<AppointmentListItem>[] = []) => {
  const appointments = [
    baseAppt(),
    {
      ...baseAppt(),
      id: "2",
      providerId: "3",
      providerName: "Dr. Lee",
      appointmentStartDatetimeUtc: "2025-01-01T09:00:00Z", // past
      appointmentEndDatetimeUtc: "2025-01-01T09:30:00Z",
      reason: "Follow-up",
      status: "COMPLETED" as const,
    },
  ];

  return appointments.map((appt, index) => ({
    ...appt,
    ...(overrides[index] || {}),
  }));
};

describe("UserAppointment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.setSystemTime(new Date("2026-01-15T12:00:00Z"));
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "patient-1" },
      loading: false,
    } as AuthCtx);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows spinner while loading", () => {
    vi.mocked(getPatientAppointments).mockImplementation(
      () => new Promise(() => {}),
    );
    render(<UserAppointment />, { wrapper: TestWrapper });
    expect(screen.getByText(/Loading appointments/)).toBeInTheDocument();
  });

  it("renders upcoming and past sections", async () => {
    vi.mocked(getPatientAppointments).mockResolvedValue(mockAppts());
    render(<UserAppointment />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("Upcoming")).toBeInTheDocument();
      expect(screen.getByText("Past")).toBeInTheDocument();
    });

    expect(screen.getByText("Dr. Smith")).toBeInTheDocument();
    expect(screen.getByText("Dr. Lee")).toBeInTheDocument();
  });

  it("shows empty messages when no appointments", async () => {
    vi.mocked(getPatientAppointments).mockResolvedValue([]);
    render(<UserAppointment />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("No upcoming appointments.")).toBeInTheDocument();
      expect(screen.getByText("No past appointments.")).toBeInTheDocument();
    });
  });

  it("shows Pay/Cancel for upcoming CONFIRMED appointment", async () => {
    vi.mocked(getPatientAppointments).mockResolvedValue(
      mockAppts({ status: "CONFIRMED" }),
    );
    render(<UserAppointment />, { wrapper: TestWrapper });

    await waitFor(() =>
      expect(screen.getByText("Dr. Smith")).toBeInTheDocument(),
    );

    expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
  });

  it("shows status badge for non-actionable upcoming appointment", async () => {
    vi.setSystemTime(new Date("2026-01-15T12:00:00Z"));

    const requestedAppointments = mockAppts([
      { status: "REQUESTED" },
      { status: "REQUESTED" },
    ]);

    vi.mocked(getPatientAppointments).mockResolvedValue(requestedAppointments);
    render(<UserAppointment />, { wrapper: TestWrapper });

    await waitFor(() =>
      expect(screen.getByText("Dr. Smith")).toBeInTheDocument(),
    );

    // Find all appointment cards
    const appointmentCards = screen.getAllByRole("article");
    const upcomingCard = appointmentCards[0];

    expect(
      within(upcomingCard).getByRole("button", { name: /Cancel/i }),
    ).toBeInTheDocument();

    // Should show REQUESTED status badge
    expect(within(upcomingCard).getByText("REQUESTED")).toBeInTheDocument();
  });

  it("uses fallback image when providerImage is null", async () => {
    vi.mocked(getPatientAppointments).mockResolvedValue(mockAppts());
    render(<UserAppointment />, { wrapper: TestWrapper });

    await waitFor(() =>
      expect(screen.getByAltText(/Dr\. Smith/)).toBeInTheDocument(),
    );
    const img = screen.getByAltText(/Dr\. Smith/) as HTMLImageElement;
    expect(img.src).toContain("profile.jpg");
  });
});
