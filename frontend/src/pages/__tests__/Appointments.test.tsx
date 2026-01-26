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
  default: ({ onSelect }: { onSelect: (isoDay: string) => void }) => (
    <button onClick={() => onSelect("2024-06-10")} data-testid="week-selector">
      Select Day
    </button>
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
});
