import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TopDoctors from "../TopDoctors";
import { useDoctor } from "../../../hooks/useDoctor";
import { MemoryRouter } from "react-router-dom";
import type { DoctorListItem, DoctorCtx } from "../../types/doctor";

vi.mock("../../../hooks/useDoctor");

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => ({
  ...(await vi.importActual("react-router-dom")),
  useNavigate: () => mockNavigate,
}));

const mockDoctors: DoctorListItem[] = [
  {
    id: 1,
    firstName: "Alice",
    lastName: "Smith",
    speciality: 1,
    specialityName: "cardiology",
    image: "alice.png",
  },
  {
    id: 2,
    firstName: "Bob",
    lastName: "Jones",
    speciality: 2,
    specialityName: "neurology",
    image: "bob.png",
  },
];

describe("TopDoctors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
  });

  it("renders doctor cards", () => {
    vi.mocked(useDoctor).mockReturnValue({
      doctors: mockDoctors,
      loading: false,
      error: null,
      getDoctors: vi.fn(),
    } as DoctorCtx);

    render(
      <MemoryRouter>
        <TopDoctors />
      </MemoryRouter>,
    );

    const cards = screen.getAllByRole("img");
    expect(cards).toHaveLength(2);
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    expect(screen.getByText("Bob Jones")).toBeInTheDocument();
  });

  it("navigates to appointment page when card clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useDoctor).mockReturnValue({
      doctors: mockDoctors,
      loading: false,
      error: null,
      getDoctors: vi.fn(),
    } as DoctorCtx);

    render(
      <MemoryRouter>
        <TopDoctors />
      </MemoryRouter>,
    );

    await user.click(screen.getByText("Alice Smith"));
    expect(mockNavigate).toHaveBeenCalledWith("/appointment/1");
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it('navigates to "/doctors" when "more" button clicked', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <TopDoctors />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /more/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/doctors");
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it("shows nothing when doctors is empty", () => {
    vi.mocked(useDoctor).mockReturnValue({
      doctors: [],
      loading: false,
      error: null,
      getDoctors: vi.fn(),
    } as DoctorCtx);

    render(
      <MemoryRouter>
        <TopDoctors />
      </MemoryRouter>,
    );

    expect(screen.queryByText("Alice Smith")).not.toBeInTheDocument();
    expect(screen.getByText("Top Doctors to Book")).toBeInTheDocument();
  });
});
