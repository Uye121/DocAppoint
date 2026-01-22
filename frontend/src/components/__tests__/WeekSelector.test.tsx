import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WeekSelector from "../WeekSelector";
import { formatISO } from "date-fns";

const mockDays: Date[] = [
  new Date("2024-01-15"),
  new Date("2024-01-16"),
  new Date("2024-01-17"),
  new Date("2024-01-18"),
  new Date("2024-01-19"),
];

beforeEach(() => {
  process.env.TZ = "UTC";
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2024-01-16T12:00:00Z"));
});

afterEach(() => {
  vi.useRealTimers();
});

describe("WeekSelector", () => {
  it("renders 5 day buttons", () => {
    render(
      <WeekSelector
        days={mockDays}
        selectedDay={formatISO(mockDays[0], { representation: "date" })}
        onSelect={vi.fn()}
      />,
    );

    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(5);
    expect(screen.getByText("Mon 15")).toBeInTheDocument();
    expect(screen.getByText("Tue 16")).toBeInTheDocument();
    expect(screen.getByText("Wed 17")).toBeInTheDocument();
    expect(screen.getByText("Thu 18")).toBeInTheDocument();
    expect(screen.getByText("Fri 19")).toBeInTheDocument();
  });

  it("highlights selected day", () => {
    render(
      <WeekSelector
        days={mockDays}
        selectedDay={formatISO(mockDays[2], { representation: "date" })}
        onSelect={vi.fn()}
      />,
    );

    const wed = screen.getByRole("button", { name: /Wed 17/i });
    // const wed = screen.getByTestId("day-2024-01-17");
    expect(wed).toHaveClass("border-b-2", "border-primary", "text-primary");
  });

  it("disables past days", () => {
    render(
      <WeekSelector
        days={mockDays}
        selectedDay={formatISO(mockDays[3], { representation: "date" })}
        onSelect={vi.fn()}
      />,
    );

    const mon = screen.getByRole("button", { name: /Mon 15/i });
    expect(mon).toBeDisabled();
    expect(mon).toHaveClass("text-gray-300", "cursor-not-allowed");
  });

  it("calls onSelect with ISO date when day clicked", async () => {
    userEvent.setup();
    const mockSelect = vi.fn();

    render(
      <WeekSelector days={mockDays} selectedDay={""} onSelect={mockSelect} />,
    );

    // Use fireevent to avoid async issue
    const thurBtn = screen.getByRole("button", { name: /Thu 18/i });
    fireEvent.click(thurBtn);

    expect(mockSelect).toHaveBeenCalledOnce();
    expect(mockSelect).toHaveBeenCalledWith("2024-01-18");
  });

  it("does not call onSelect for past day", async () => {
    userEvent.setup();
    const mockSelect = vi.fn();

    render(
      <WeekSelector days={mockDays} selectedDay={""} onSelect={mockSelect} />,
    );

    const monBtn = screen.getByRole("button", { name: /Mon 15/i });
    fireEvent.click(monBtn);
    expect(mockSelect).not.toHaveBeenCalled();
  });
});
