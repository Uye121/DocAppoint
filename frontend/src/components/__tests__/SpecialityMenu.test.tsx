import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SpecialtyMenu from "../SpecialtyMenu";
import { useSpeciality } from "../../../hooks/useSpeciality";
import type { SpecialityCtx, Speciality } from "../../types/speciality";

vi.mock("../../../hooks/useSpeciality");

const mockSpecialities: Speciality[] = [
  { id: 1, name: "Cardiology", image: "cardio.png" },
  { id: 2, name: "Neurology", image: "neuro.png" },
];

describe("SpecialtyMenu", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
  });

  it("renders speciality cards and links", () => {
    vi.mocked(useSpeciality).mockReturnValue({
      specialities: mockSpecialities,
      loading: false,
      error: null,
      getSpecialities: vi.fn(),
    } as SpecialityCtx);

    render(
      <MemoryRouter>
        <SpecialtyMenu />
      </MemoryRouter>,
    );

    expect(screen.getByText("Cardiology")).toBeInTheDocument();
    expect(screen.getByText("Neurology")).toBeInTheDocument();
    expect(screen.getAllByRole("link")).toHaveLength(2);
  });

  it("shows loading spinner while loading", () => {
    vi.mocked(useSpeciality).mockReturnValue({
      specialities: null,
      loading: true,
      error: null,
      getSpecialities: vi.fn(),
    } as SpecialityCtx);

    render(<SpecialtyMenu />);

    expect(screen.getByText("Retrieving data...")).toBeInTheDocument();
  });

  it("shows error message on failure", () => {
    vi.mocked(useSpeciality).mockReturnValue({
      specialities: null,
      loading: false,
      error: "Network error",
      getSpecialities: vi.fn(),
    } as SpecialityCtx);

    render(<SpecialtyMenu />);

    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("scrolls to top when a speciality is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useSpeciality).mockReturnValue({
      specialities: mockSpecialities,
      loading: false,
      error: null,
      getSpecialities: vi.fn(),
    } as SpecialityCtx);

    render(
      <MemoryRouter>
        <SpecialtyMenu />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("link", { name: /cardiology/i }));
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });
});
