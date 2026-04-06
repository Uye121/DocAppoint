import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import Appointments from "../Appointments";

vi.mock("../../api/doctor", () => ({
  getDoctorById: vi.fn(),
}));

vi.mock("../../api/appointment", () => ({
  getSlotsByRange: vi.fn(),
  scheduleAppointment: vi.fn(),
}));

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../components/DoctorCard", () => ({
  default: () => <div data-testid="doctor-card">Doctor Card</div>,
}));

vi.mock("../../components/RelatedDoctors", () => ({
  default: () => <div data-testid="related-doctors">Related Doctors</div>,
}));

vi.mock("../../components/Spinner", () => ({
  default: ({ loadingText }: { loadingText: string }) => (
    <div data-testid="spinner">{loadingText || "Loading..."}</div>
  ),
}));

vi.mock("../../components/WeekSelector", () => ({
  default: ({
    onSelect,
    goToCurrentWeek,
    onWeekChange,
    weekOffset,
  }: {
    onSelect: (isoDay: string) => void;
    goToCurrentWeek: () => void;
    onWeekChange: (delta: number) => void;
    weekOffset: number;
  }) => (
    <div data-testid="week-selector">
      <button onClick={() => onSelect("2024-06-10")} data-testid="select-day">
        Select Day
      </button>
      <button onClick={() => onWeekChange(-1)} data-testid="prev-week">
        Previous Week
      </button>
      <button onClick={goToCurrentWeek} data-testid="current-week">
        Current Week
      </button>
      <button onClick={() => onWeekChange(1)} data-testid="next-week">
        Next Week
      </button>
      <span data-testid="week-offset">Offset: {weekOffset}</span>
    </div>
  ),
}));

vi.mock("../../components/SlotList", () => ({
  default: ({ onSelect }: { onSelect: (slot: Slot) => void }) => (
    <button
      onClick={() =>
        onSelect({
          id: "slot-1",
          start: "2024-06-10T09:00:00Z",
          end: "2024-06-10T09:30:00Z",
          hospitalId: 1,
          hospitalName: "General Hospital",
          hospitalTimezone: "UTC",
          status: "FREE",
        })
      }
      data-testid="slot-list"
    >
      Select Slot
    </button>
  ),
}));

// Import mocked functions
import { getDoctorById } from "../../api/doctor";
import { getSlotsByRange, scheduleAppointment } from "../../api/appointment";
import { useAuth } from "../../../hooks/useAuth";
import type { Slot } from "../../types/appointment";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        suspense: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

const mockUser = { id: "user-123", email: "test@example.com" };

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <MemoryRouter initialEntries={["/appointment/10"]}>
      <QueryClientProvider client={createTestQueryClient()}>
        <Routes>
          <Route path="/appointment/:docId" element={children} />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>
  );
};

describe("Appointments page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.setSystemTime(new Date("2024-06-10T12:00:00Z"));

    // Default mock implementations
    vi.mocked(useAuth).mockReturnValue({ user: mockUser });
    vi.mocked(getDoctorById).mockResolvedValue({
      user: {
        firstName: "John",
        lastName: "Doe",
        image: "image-url",
      },
      education: "MD",
      specialityName: "Cardiology",
      yearsOfExperience: 10,
      about: "About doctor",
      fees: 100,
    });

    vi.mocked(getSlotsByRange).mockResolvedValue({
      "2024-06-10": [
        {
          id: "slot-1",
          start: "2024-06-10T09:00:00Z",
          end: "2024-06-10T09:30:00Z",
          hospitalId: 1,
        },
      ],
      "2024-06-17": [
        {
          id: "slot-2",
          start: "2024-06-17T09:00:00Z",
          end: "2024-06-17T09:30:00Z",
          hospitalId: 1,
        },
      ],
    });

    vi.mocked(scheduleAppointment).mockResolvedValue({
      id: "appointment-123",
      status: "confirmed",
    });
  });

  it("integrates all components and manages booking state", async () => {
    const user = userEvent.setup();

    render(<Appointments />, { wrapper: TestWrapper });

    // Verify page orchestrates loading
    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Test page's slot selection logic
    await user.click(screen.getByTestId("slot-list"));

    // Test page's form state management
    const reasonInput = screen.getByPlaceholderText(/Briefly describe/i);
    await user.type(reasonInput, "Test reason");

    // Test page's booking submission
    await user.click(screen.getByRole("button", { name: /book/i }));

    // 5. Verify page makes correct API call
    expect(scheduleAppointment).toHaveBeenCalledWith(
      expect.objectContaining({
        provider: "10",
        patient: "user-123",
        reason: "Test reason",
      }),
    );
  });

  it("disables booking when no slot is selected", async () => {
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Verify slot list is present but NOT clicked
    expect(screen.getByTestId("slot-list")).toBeInTheDocument();

    // Button should be disabled because no slot selected
    const bookButton = screen.getByRole("button", { name: /book/i });
    expect(bookButton).toBeDisabled();

    // Optional: verify reason textarea is NOT rendered (since no slot selected)
    expect(
      screen.queryByPlaceholderText(/Briefly describe/i),
    ).not.toBeInTheDocument();
  });

  it("disables booking when slot is selected but no reason provided", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Select a slot
    await user.click(screen.getByTestId("slot-list"));

    // Reason textarea should now appear
    expect(
      screen.getByPlaceholderText(/Briefly describe/i),
    ).toBeInTheDocument();

    // But button still disabled because reason is empty
    const bookButton = screen.getByRole("button", { name: /book/i });
    expect(bookButton).toBeDisabled();
  });

  it("handles next week navigation correctly", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Initially at week 0
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 0");

    // Click next week
    await user.click(screen.getByTestId("next-week"));

    // Week offset should update
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 1");

    // Should fetch slots for new week
    await waitFor(() => {
      expect(getSlotsByRange).toHaveBeenCalledWith(
        expect.objectContaining({
          providerId: "10",
        }),
      );
    });
  });

  it("handles previous week navigation correctly", async () => {
    const user = userEvent.setup();

    // Start at week 1 by setting initial state through navigation
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // First go to next week
    await user.click(screen.getByTestId("next-week"));
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 1");

    // Then go back
    await user.click(screen.getByTestId("prev-week"));
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 0");
  });

  it("prevents navigating before min offset (0)", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Already at offset 0
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 0");

    // Try to go previous
    await user.click(screen.getByTestId("prev-week"));

    // Should still be at 0
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 0");
  });

  it("prevents navigating beyond max offset (2)", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Navigate to max offset
    await user.click(screen.getByTestId("next-week")); // offset 1
    await user.click(screen.getByTestId("next-week")); // offset 2
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 2");

    // Try to go beyond max
    await user.click(screen.getByTestId("next-week"));

    // Should still be at 2
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 2");
  });

  it("goes to current week when Current Week button is clicked", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Navigate to a different week
    await user.click(screen.getByTestId("next-week"));
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 1");

    // Click current week
    await user.click(screen.getByTestId("current-week"));

    // Should reset to offset 0
    expect(screen.getByTestId("week-offset")).toHaveTextContent("Offset: 0");
  });

  it("updates selected day when day is selected", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Click select day button
    await user.click(screen.getByTestId("select-day"));

    // Should fetch slots for the new day
    await waitFor(() => {
      expect(getSlotsByRange).toHaveBeenCalled();
    });
  });

  it("resets booked state when week changes", async () => {
    const user = userEvent.setup();
    render(<Appointments />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByTestId("doctor-card")).toBeInTheDocument();
    });

    // Complete a booking
    await user.click(screen.getByTestId("slot-list"));
    const reasonInput = screen.getByPlaceholderText(/Briefly describe/i);
    await user.type(reasonInput, "Test reason");
    await user.click(screen.getByRole("button", { name: /book/i }));

    // Verify booking success message appears
    await waitFor(() => {
      expect(
        screen.getByText(/Appointment requested successfully/i),
      ).toBeInTheDocument();
    });

    // Change week (this will reset selectedDay and clear booked state)
    await user.click(screen.getByTestId("next-week"));

    // Booked message should disappear
    await waitFor(() => {
      expect(
        screen.queryByText(/Appointment requested successfully/i),
      ).not.toBeInTheDocument();
    });
  });
});
