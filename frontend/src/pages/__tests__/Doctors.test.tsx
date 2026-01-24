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
});
