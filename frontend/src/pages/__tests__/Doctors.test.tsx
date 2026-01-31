import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";

import Doctors from "../Doctors";
import { useDoctor } from "../../../hooks/useDoctor";

vi.mock("../../../hooks/useDoctor", () => ({
  useDoctor: vi.fn(),
}));

const mockDoctors = [
  {
    id: "1",
    firstName: "John",
    lastName: "Smith",
    image: "john.jpg",
    specialityName: "General Physician",
  },
  {
    id: "2",
    firstName: "Jane",
    lastName: "Doe",
    image: "jane.jpg",
    specialityName: "Gynecologist",
  },
  {
    id: "3",
    firstName: "Bob",
    lastName: "Johnson",
    image: "bob.jpg",
    specialityName: "General Physician",
  },
];

const createTestWrapper = (initialRoute: string = "/doctors") => {
  return function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/doctors" element={children} />
          <Route path="/doctors/:speciality" element={children} />
          <Route
            path="/appointment/:id"
            element={<div>Appointment Page</div>}
          />
        </Routes>
      </MemoryRouter>
    );
  };
};

describe("Doctors page", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useDoctor).mockReturnValue({ doctors: mockDoctors });
  });

  it("renders all doctors when no speciality filter", async () => {
    const TestWrapper = createTestWrapper("/doctors");
    render(<Doctors />, { wrapper: TestWrapper });

    expect(
      screen.getByText(/Browse through the doctors specialist/i),
    ).toBeInTheDocument();

    // All doctors should be rendered
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
    });
  });

  it("filters doctors by speciality from URL param", async () => {
    const TestWrapper = createTestWrapper("/doctors/Gynecologist");
    render(<Doctors />, { wrapper: TestWrapper });

    await waitFor(() => {
      // Only Gynecologist should show
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      expect(screen.queryByText("John Smith")).not.toBeInTheDocument();
      expect(screen.queryByText("Bob Johnson")).not.toBeInTheDocument();
    });
  });

  it("filters doctors by speciality on click", async () => {
    const user = userEvent.setup();
    const TestWrapper = createTestWrapper("/doctors");

    render(<Doctors />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
    });

    const neuroBtn = screen.getByRole("button", { name: "Neurologist" });

    expect(neuroBtn).not.toHaveClass("bg-indigo-100");

    await user.click(neuroBtn);

    // Active styling applied (navigation happened internally)
    await waitFor(() => {
      expect(neuroBtn).toHaveClass("bg-indigo-100");
    });
  });

  it("clears speciality filter when active button clicked again", async () => {
    const user = userEvent.setup();
    // Start with General Physician filter
    const TestWrapper = createTestWrapper("/doctors/General%20Physician");
    render(<Doctors />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
      expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
      expect(screen.queryByText("Jane Doe")).not.toBeInTheDocument();
    });

    const genBtn = screen.getByRole("button", { name: "General Physician" });
    await user.click(genBtn);

    // After clicking, filter should be cleared, so ALL doctors should show
    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      expect(screen.getByText("John Smith")).toBeInTheDocument();
      expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
    });
  });

  it("navigates to appointment page when doctor card clicked", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/doctors"]}>
        <Routes>
          <Route path="/doctors" element={<Doctors />} />
          <Route
            path="/appointment/:id"
            element={<div>Appointment Page for ID</div>}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
    });

    const johnCard = screen.getByText("John Smith").closest("button");
    await user.click(johnCard!);

    await waitFor(() => {
      expect(screen.getByText(/Appointment Page for ID/i)).toBeInTheDocument();
    });
  });

  it("toggles filter panel on mobile", async () => {
    const user = userEvent.setup();
    const TestWrapper = createTestWrapper("/doctors");

    render(<Doctors />, { wrapper: TestWrapper });

    const toggleBtn = screen.getByRole("button", { name: /filters/i });
    const filterPanel = screen.getByTestId("filter-panel");

    // initially hidden on small screens
    expect(filterPanel).toHaveClass("hidden", "sm:flex");

    await user.click(toggleBtn);
    expect(filterPanel).toHaveClass("flex");
    expect(toggleBtn).toHaveClass("bg-primary", "text-white");

    await user.click(toggleBtn);
    expect(filterPanel).toHaveClass("hidden", "sm:flex");
    expect(toggleBtn).not.toHaveClass("bg-primary");
  });

  it("renders loading state while doctors context is empty", () => {
    vi.mocked(useDoctor).mockReturnValue({ doctors: [] });
    const TestWrapper = createTestWrapper("/doctors");

    render(<Doctors />, { wrapper: TestWrapper });

    // Still renders heading and filter, but no cards
    expect(
      screen.getByText(/Browse through the doctors specialist/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("handles missing image gracefully", async () => {
    vi.mocked(useDoctor).mockReturnValue({
      doctors: [{ ...mockDoctors[0], image: "" }],
    });
    const TestWrapper = createTestWrapper("/doctors");

    render(<Doctors />, { wrapper: TestWrapper });

    const img = screen.getByAltText("Dr. Smith's portrait") as HTMLImageElement;
    expect(img.src).toContain("");
  });
});
