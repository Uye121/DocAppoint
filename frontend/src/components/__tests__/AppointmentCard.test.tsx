import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import AppointmentCard from "../AppointmentCard";
import type { AppointmentListItem } from "../../types/appointment";

vi.mock("../../api/appointment", () => ({
  updateAppointmentStatus: vi.fn(),
}));

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

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

import { updateAppointmentStatus } from "../../api/appointment";

describe("AppointmentCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders provider name, formatted date, and reason", () => {
    render(<AppointmentCard item={mockAppointment()} userId="u1" />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText("Dr. Smith")).toBeInTheDocument();
    expect(screen.getByText(/Routine check-up/)).toBeInTheDocument();

    // Check that date formatting is applied (without testing exact format)
    const dateElement = screen.getByText(/\w+, \w+ \d+ at \d+:\d+ (AM|PM)/);
    expect(dateElement).toBeInTheDocument();
  });

  it("shows fallback image when providerImage is null", () => {
    render(
      <AppointmentCard
        item={mockAppointment({ providerImage: null })}
        userId="u1"
      />,
      {
        wrapper: createWrapper(),
      },
    );

    const img = screen.getByAltText("Dr. Smith's profile");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src");
  });

  it("uses provided providerImage when available", () => {
    render(
      <AppointmentCard
        item={mockAppointment({ providerImage: "https://example.com/dr.jpg" })}
        userId="u1"
      />,
      { wrapper: createWrapper() },
    );

    const img = screen.getByAltText("Dr. Smith's profile");
    expect(img).toHaveAttribute("src", "https://example.com/dr.jpg");
  });

  it("displays correct status badge based on appointment status", () => {
    const statuses = [
      { status: "REQUESTED", expectedClass: "bg-status-requested" },
      { status: "CONFIRMED", expectedClass: "bg-status-confirmed" },
      { status: "COMPLETED", expectedClass: "bg-status-completed" },
      { status: "RESCHEDULED", expectedClass: "bg-status-rescheduled" },
      { status: "CANCELLED", expectedClass: "bg-status-cancelled" },
    ] as const;

    statuses.forEach(({ status, expectedClass }) => {
      const { unmount } = render(
        <AppointmentCard item={mockAppointment({ status })} userId="u1" />,
        { wrapper: createWrapper() },
      );

      const statusBadge = screen.getByText(status);
      expect(statusBadge).toBeInTheDocument();
      expect(statusBadge).toHaveClass(expectedClass);
      unmount();
    });
  });

  it("shows Cancel button for appropriate statuses when not past appointment", () => {
    const statusesWithButton: AppointmentListItem["status"][] = [
      "CONFIRMED",
      "COMPLETED",
      "REQUESTED",
    ];
    const statusesWithoutButton: AppointmentListItem["status"][] = [
      "RESCHEDULED",
      "CANCELLED",
    ];

    statusesWithButton.forEach((status) => {
      const { unmount } = render(
        <AppointmentCard item={mockAppointment({ status })} userId="u1" />,
        { wrapper: createWrapper() },
      );

      expect(
        screen.getByRole("button", { name: /cancel appointment/i }),
      ).toBeInTheDocument();
      unmount();
    });

    statusesWithoutButton.forEach((status) => {
      const { unmount } = render(
        <AppointmentCard item={mockAppointment({ status })} userId="u1" />,
        { wrapper: createWrapper() },
      );

      expect(
        screen.queryByRole("button", { name: /cancel appointment/i }),
      ).not.toBeInTheDocument();
      unmount();
    });
  });

  it("does not show Cancel button for past appointments", () => {
    render(
      <AppointmentCard
        item={mockAppointment({ status: "CONFIRMED" })}
        userId="u1"
        isPast={true}
      />,
      { wrapper: createWrapper() },
    );

    expect(
      screen.queryByRole("button", { name: /cancel appointment/i }),
    ).not.toBeInTheDocument();
  });

  it("calls updateAppointmentStatus with correct parameters when Cancel button is clicked", async () => {
    const mockUpdate = vi
      .mocked(updateAppointmentStatus)
      .mockResolvedValue(undefined);

    render(<AppointmentCard item={mockAppointment()} userId="u1" />, {
      wrapper: createWrapper(),
    });

    const cancelButton = screen.getByRole("button", {
      name: /cancel appointment/i,
    });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith("1", "CANCELLED");
    });
  });
});
