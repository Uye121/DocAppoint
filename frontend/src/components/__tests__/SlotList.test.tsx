import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SlotList from "../SlotList";
import { formatInTimeZone } from "date-fns-tz";
import type { Slot } from "../../types/appointment";

// Mock date-fns-tz
vi.mock("date-fns-tz", () => ({
  formatInTimeZone: vi.fn(),
}));

// Mock current date for consistent testing
const mockCurrentDate = new Date("2024-01-15T12:00:00Z"); // 7AM NY

describe("SlotList", () => {
  const mockSlots: Slot[] = [
    {
      id: "1",
      hospitalId: 1,
      start: "2024-01-15T14:00:00Z",
      end: "2024-01-15T14:30:00Z",
      status: "FREE",
      hospitalName: "General Hospital",
      hospitalTimezone: "America/New_York",
    },
    {
      id: "2",
      hospitalId: 1,
      start: "2024-01-15T15:00:00Z",
      end: "2024-01-15T15:30:00Z",
      status: "BOOKED",
      hospitalName: "City Clinic",
      hospitalTimezone: "America/Chicago",
    },
    {
      id: "3",
      hospitalId: 1,
      start: "2024-01-15T06:00:00Z",
      end: "2024-01-15T10:30:00Z",
      status: "FREE",
      hospitalName: "Community Health",
      hospitalTimezone: "America/New_York",
    },
  ];

  const defaultProps = {
    slots: mockSlots,
    userTz: "America/New_York",
    selectedId: null,
    onSelect: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    vi.setSystemTime(mockCurrentDate);

    // Setup default formatInTimeZone mock responses
    vi.mocked(formatInTimeZone).mockImplementation((date, tz, formatStr) => {
      if (formatStr === "yyyy-MM-dd HH:mm:ss") {
        const d = new Date(date);

        if (d.getTime() === mockCurrentDate.getTime()) {
          return "2024-01-15 07:00:00";
        }
        if (d.getTime() === new Date(mockSlots[0].start).getTime()) {
          return "2024-01-15 09:00:00";
        }
        if (d.getTime() === new Date(mockSlots[1].start).getTime()) {
          return "2024-01-15 10:00:00";
        }
        if (d.getTime() === new Date(mockSlots[2].start).getTime()) {
          return "2024-01-15 01:00:00";
        }
      }
      if (formatStr === "HH:mm") {
        if (date === mockSlots[0].start) return "09:00";
        if (date === mockSlots[0].end) return "09:30";
        if (date === mockSlots[1].start) return "10:00";
        if (date === mockSlots[1].end) return "10:30";
        if (date === mockSlots[2].start) return "01:00";
        if (date === mockSlots[2].end) return "01:30";
      }
      return "";
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders 'No available slots' message when slots array is empty", () => {
    render(<SlotList {...defaultProps} slots={[]} />);

    expect(
      screen.getByText("No available slots this day."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders all slots with correct time formatting", () => {
    render(<SlotList {...defaultProps} />);

    // Check all slots are rendered
    expect(screen.getAllByRole("button")).toHaveLength(3);

    // Check time formatting
    expect(screen.getByText("09:00 – 09:30")).toBeInTheDocument();
    expect(screen.getByText("10:00 – 10:30")).toBeInTheDocument();
    expect(screen.getByText("01:00 – 01:30")).toBeInTheDocument();

    // Check hospital names
    expect(screen.getByText("General Hospital")).toBeInTheDocument();
    expect(screen.getByText("City Clinic")).toBeInTheDocument();
    expect(screen.getByText("Community Health")).toBeInTheDocument();
  });

  it("enables free future slots and allows selection", () => {
    render(<SlotList {...defaultProps} />);

    const freeSlot = screen.getAllByRole("button")[0];

    // Should be enabled (free and not past)
    expect(freeSlot).not.toBeDisabled();
    expect(freeSlot.className).toContain("border-gray-200");
    expect(freeSlot.className).toContain("hover:border-gray-400");

    // Click the slot
    fireEvent.click(freeSlot);

    expect(defaultProps.onSelect).toHaveBeenCalledWith(mockSlots[0]);
    expect(defaultProps.onSelect).toHaveBeenCalledTimes(1);
  });

  it("disables booked slots", () => {
    render(<SlotList {...defaultProps} />);

    const bookedSlot = screen.getAllByRole("button")[1];

    // Should have disabled styling
    expect(bookedSlot.className).toContain("border-red-300");
    expect(bookedSlot.className).toContain("bg-red-50");
    expect(bookedSlot.className).toContain("text-red-700");
    expect(bookedSlot.className).toContain("cursor-not-allowed");

    // Click should not trigger onSelect
    fireEvent.click(bookedSlot);
    expect(defaultProps.onSelect).not.toHaveBeenCalled();
  });

  it("disables past slots even if free", () => {
    render(<SlotList {...defaultProps} />);

    const pastSlot = screen.getAllByRole("button")[2];

    // Should have disabled styling
    expect(pastSlot.className).toContain("border-red-300");
    expect(pastSlot.className).toContain("bg-red-50");
    expect(pastSlot.className).toContain("text-red-700");
    expect(pastSlot.className).toContain("cursor-not-allowed");

    // Click should not trigger onSelect
    fireEvent.click(pastSlot);
    expect(defaultProps.onSelect).not.toHaveBeenCalled();
  });

  it("uses default timezone when hospitalTimezone is not provided", () => {
    const slotWithoutTz: Slot = {
      id: "4",
      hospitalId: 1,
      start: new Date("2024-01-15T16:00:00Z"),
      end: new Date("2024-01-15T16:30:00Z"),
      status: "FREE",
      hospitalName: "Test Hospital",
      // No hospitalTimezone
    };

    render(<SlotList {...defaultProps} slots={[slotWithoutTz]} />);

    // Should call formatInTimeZone with default timezone
    expect(formatInTimeZone).toHaveBeenCalledWith(
      expect.any(Date),
      "America/New_York",
      "yyyy-MM-dd HH:mm:ss",
    );
  });

  it("correctly compares times for past/future determination", () => {
    const { rerender } = render(
      <SlotList {...defaultProps} slots={[mockSlots[0]]} />,
    );
    const futureBtn = screen.getByRole("button", { name: /09:00 – 09:30/i });
    expect(futureBtn).toHaveClass("border-gray-200");

    rerender(<SlotList {...defaultProps} slots={[mockSlots[2]]} />);
    const pastBtn = screen.getByRole("button", { name: /01:00 – 01:30/i });
    expect(pastBtn).toHaveClass("border-red-300");
  });

  it("calls onSelect only with valid slots", () => {
    const onSelect = vi.fn();
    render(<SlotList {...defaultProps} onSelect={onSelect} />);

    const buttons = screen.getAllByRole("button");

    // Click free slot (should work)
    fireEvent.click(buttons[0]);
    expect(onSelect).toHaveBeenCalledWith(mockSlots[0]);

    // Click booked slot (should not work)
    fireEvent.click(buttons[1]);
    expect(onSelect).toHaveBeenCalledTimes(1);

    // Click past slot (should not work)
    fireEvent.click(buttons[2]);
    expect(onSelect).toHaveBeenCalledTimes(1);
  });
});
