import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AppointmentCard from "../AppointmentCard";
import { assets } from "../../assets/assets_frontend/assets";
import type { AppointmentListItem } from "../../types/appointment";

const mockAppointment = (overrides?: Partial<AppointmentListItem>) =>
  ({
    id: "1",
    patientId: "p1",
    providerId: "d1",
    patientName: "Pat",
    providerName: "Dr. Smith",
    providerImage: null,
    appointmentStartDatetimeUtc: "2026-01-30T10:00:00Z",
    appointmentEndDatetimeUtc: "2026-01-30T10:30:00Z",
    location: "General Hospital",
    reason: "Routine check-up",
    status: "CONFIRMED",
    ...overrides,
  }) as AppointmentListItem;

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(() => ({ user: { id: "u1" }, loading: false })),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({ data: [], isLoading: false, refetch: vi.fn() })),
}));

describe("AppointmentCard", () => {
  beforeEach(() => {
    vi.spyOn(Intl.DateTimeFormat.prototype, "resolvedOptions").mockReturnValue({
      timeZone: "UTC",
    } as Intl.ResolvedDateTimeFormatOptions);
  });
  afterEach(() => vi.restoreAllMocks());

  it("renders provider name, date, reason", () => {
    render(<AppointmentCard item={mockAppointment()} />);
    expect(screen.getByText("Dr. Smith")).toBeInTheDocument();
    expect(screen.getByText(/Friday, Jan 30 at 10:00 AM/)).toBeInTheDocument();
    expect(screen.getByText("Routine check-up")).toBeInTheDocument();
  });

  it("shows fallback image when providerImage is null", () => {
    render(<AppointmentCard item={mockAppointment({ providerImage: null })} />);
    const img = screen.getByRole("img") as HTMLImageElement;
    expect(img.src).toContain(assets.profile_pic);
  });

  it("uses provided providerImage", () => {
    render(
      <AppointmentCard
        item={mockAppointment({ providerImage: "https://example.com/dr.jpg" })}
      />,
    );
    const img = screen.getByRole("img") as HTMLImageElement;
    expect(img.src).toBe("https://example.com/dr.jpg");
  });

  it("displays Pay/Cancel buttons for upcoming CONFIRMED appointment", () => {
    render(<AppointmentCard item={mockAppointment({ status: "CONFIRMED" })} />);
    expect(screen.getByText("Pay Now")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("hides buttons and shows status badge for non-actionable status", () => {
    render(<AppointmentCard item={mockAppointment({ status: "REQUESTED" })} />);
    expect(
      screen.queryByRole("button", { name: /pay now/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("REQUESTED")).toBeInTheDocument();
  });

  it("applies correct status colour class", () => {
    const { rerender } = render(
      <AppointmentCard item={mockAppointment({ status: "REQUESTED" })} />,
    );
    expect(screen.getByText("REQUESTED")).toHaveClass("bg-status-requested");

    rerender(
      <AppointmentCard item={mockAppointment({ status: "CANCELLED" })} />,
    );
    expect(screen.getByText("CANCELLED")).toHaveClass("bg-status-cancelled");
  });

  it("applies past-card background when isPast=true", () => {
    const { container } = render(
      <AppointmentCard item={mockAppointment()} isPast />,
    );
    expect(container.firstChild).toHaveClass("bg-surface");
  });

  it("does NOT apply hover styles for past cards", () => {
    const { container } = render(
      <AppointmentCard item={mockAppointment()} isPast />,
    );
    expect(container.firstChild).not.toHaveClass("hover:card-hover");
  });
});
