import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WeekSelector from "../WeekSelector";

const defaultProps = {
  selectedDay: "2024-01-16",
  onSelect: vi.fn(),
  goToCurrentWeek: vi.fn(),
  weekOffset: 0,
  onWeekChange: vi.fn(),
  maxWeekOffset: 2,
  minWeekOffset: 0,
};

beforeEach(() => {
  process.env.TZ = "UTC";
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2024-01-16T12:00:00Z"));
});

afterEach(() => {
  vi.useRealTimers();
});

describe("WeekSelector", () => {
  it("renders 5 day buttons for current week", () => {
    render(<WeekSelector {...defaultProps} />);

    const buttons = screen.getAllByRole("button");
    const dateButtons = buttons.filter((button) =>
      /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d+$/.test(button.textContent || ""),
    );

    expect(dateButtons).toHaveLength(7);
    expect(screen.getByText("Mon 15")).toBeInTheDocument();
    expect(screen.getByText("Tue 16")).toBeInTheDocument();
    expect(screen.getByText("Wed 17")).toBeInTheDocument();
    expect(screen.getByText("Thu 18")).toBeInTheDocument();
    expect(screen.getByText("Fri 19")).toBeInTheDocument();

    expect(screen.getByText("← Previous")).toBeInTheDocument();
    expect(screen.getByText("Current Week")).toBeInTheDocument();
    expect(screen.getByText("Next →")).toBeInTheDocument();
  });

  it("highlights selected day", () => {
    render(<WeekSelector {...defaultProps} selectedDay="2024-01-17" />);

    const wed = screen.getByRole("button", { name: /Wed 17/i });
    expect(wed).toHaveClass("border-b-2", "border-primary", "text-primary");
  });

  it("disables past days", () => {
    render(<WeekSelector {...defaultProps} />);

    const mon = screen.getByRole("button", { name: /Mon 15/i });
    expect(mon).toBeDisabled();
    expect(mon).toHaveClass("text-gray-300", "cursor-not-allowed");
  });

  it("enables current and future days", () => {
    render(<WeekSelector {...defaultProps} />);

    const tue = screen.getByRole("button", { name: /Tue 16/i });
    const wed = screen.getByRole("button", { name: /Wed 17/i });
    const thu = screen.getByRole("button", { name: /Thu 18/i });
    const fri = screen.getByRole("button", { name: /Fri 19/i });

    expect(tue).not.toBeDisabled();
    expect(wed).not.toBeDisabled();
    expect(thu).not.toBeDisabled();
    expect(fri).not.toBeDisabled();
  });

  it("calls onSelect with ISO date when day clicked", async () => {
    userEvent.setup();
    const mockSelect = vi.fn();

    render(<WeekSelector {...defaultProps} onSelect={mockSelect} />);

    // Use fireevent to avoid async issue
    const thurBtn = screen.getByRole("button", { name: /Thu 18/i });
    fireEvent.click(thurBtn);

    expect(mockSelect).toHaveBeenCalledOnce();
    expect(mockSelect).toHaveBeenCalledWith("2024-01-18");
  });

  it("does not call onSelect for past day", async () => {
    userEvent.setup();
    const mockSelect = vi.fn();

    render(<WeekSelector {...defaultProps} onSelect={mockSelect} />);

    const monBtn = screen.getByRole("button", { name: /Mon 15/i });
    fireEvent.click(monBtn);
    expect(mockSelect).not.toHaveBeenCalled();
  });

  it("renders Previous, Current Week, and Next buttons", () => {
    render(<WeekSelector {...defaultProps} />);

    expect(screen.getByText("← Previous")).toBeInTheDocument();
    expect(screen.getByText("Current Week")).toBeInTheDocument();
    expect(screen.getByText("Next →")).toBeInTheDocument();
  });

  it("disables Previous button when at minimum offset", () => {
    render(<WeekSelector {...defaultProps} weekOffset={0} minWeekOffset={0} />);

    const prevButton = screen.getByText("← Previous");
    expect(prevButton).toBeDisabled();
  });

  it("enables Previous button when not at minimum offset", () => {
    render(<WeekSelector {...defaultProps} weekOffset={1} minWeekOffset={0} />);

    const prevButton = screen.getByText("← Previous");
    expect(prevButton).not.toBeDisabled();
  });

  it("disables Next button when at maximum offset", () => {
    render(<WeekSelector {...defaultProps} weekOffset={2} maxWeekOffset={2} />);

    const nextButton = screen.getByText("Next →");
    expect(nextButton).toBeDisabled();
  });

  it("calls onWeekChange with -1 when Previous clicked", () => {
    const mockWeekChange = vi.fn();
    render(
      <WeekSelector
        {...defaultProps}
        weekOffset={1}
        onWeekChange={mockWeekChange}
      />,
    );

    const prevButton = screen.getByText("← Previous");
    fireEvent.click(prevButton);

    expect(mockWeekChange).toHaveBeenCalledOnce();
    expect(mockWeekChange).toHaveBeenCalledWith(-1);
  });

  it("calls onWeekChange with 1 when Next clicked", () => {
    const mockWeekChange = vi.fn();
    render(
      <WeekSelector
        {...defaultProps}
        weekOffset={1}
        onWeekChange={mockWeekChange}
      />,
    );

    const nextButton = screen.getByText("Next →");
    fireEvent.click(nextButton);

    expect(mockWeekChange).toHaveBeenCalledOnce();
    expect(mockWeekChange).toHaveBeenCalledWith(1);
  });

  it("calls goToCurrentWeek when Current Week button clicked", () => {
    const mockGoToCurrentWeek = vi.fn();
    render(
      <WeekSelector {...defaultProps} goToCurrentWeek={mockGoToCurrentWeek} />,
    );

    const currentWeekButton = screen.getByText("Current Week");
    fireEvent.click(currentWeekButton);

    expect(mockGoToCurrentWeek).toHaveBeenCalledOnce();
  });

  it("displays correct days when weekOffset is 1 (next week)", () => {
    render(<WeekSelector {...defaultProps} weekOffset={1} />);

    // Next week should be Jan 22-26, 2024
    expect(screen.getByText("Mon 22")).toBeInTheDocument();
    expect(screen.getByText("Tue 23")).toBeInTheDocument();
    expect(screen.getByText("Wed 24")).toBeInTheDocument();
    expect(screen.getByText("Thu 25")).toBeInTheDocument();
    expect(screen.getByText("Fri 26")).toBeInTheDocument();
  });
});
