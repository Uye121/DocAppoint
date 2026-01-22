import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import RelatedDoctors from "../RelatedDoctors";
import { useDoctor } from "../../../hooks/useDoctor";
import { MemoryRouter } from "react-router-dom";
import { DoctorCtx, type DoctorListItem } from "../../types/doctor";

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
    specialityName: "Cardiology",
    image: "img1.jpg",
  },
  {
    id: 2,
    firstName: "Bob",
    lastName: "Jones",
    speciality: 1,
    specialityName: "Cardiology",
    image: "img2.jpg",
  },
  {
    id: 3,
    firstName: "Carol",
    lastName: "White",
    speciality: 2,
    specialityName: "Neurology",
    image: "img3.jpg",
  },
];

describe("RelatedDoctors", () => {
  beforeEach(() => {
    vi.mocked(useDoctor).mockReturnValue({
      doctors: mockDoctors,
      loading: false,
      error: null,
      getDoctors: vi.fn(),
    } as DoctorCtx);
    mockNavigate.mockClear();
    vi.spyOn(window, "scrollTo").mockImplementation(() => {});
  });

  it("renders only doctors with the same speciality (excluding current doctor)", () => {
    render(
      <MemoryRouter>
        <RelatedDoctors docId="1" speciality="Cardiology" />
      </MemoryRouter>,
    );

    // Alice (id=1) is excluded; Bob (id=2) is shown
    expect(screen.getByText("Bob Jones")).toBeInTheDocument();
    expect(screen.queryByText("Alice Smith")).not.toBeInTheDocument();
    expect(screen.queryByText("Carol White")).not.toBeInTheDocument();
  });

  it("navigates to appointment page when card clicked", async () => {
    const user = userEvent.setup();
    render(<RelatedDoctors docId="1" speciality="Cardiology" />);

    await user.click(screen.getByText("Bob Jones"));

    expect(mockNavigate).toHaveBeenCalledWith("/appointment/2");
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it("shows empty state when no related doctors", () => {
    vi.mocked(useDoctor).mockReturnValue({
      doctors: [],
      loading: false,
      error: null,
      getDoctors: vi.fn(),
    } as DoctorCtx);
    render(<RelatedDoctors docId="1" speciality="Cardiology" />);

    expect(screen.getByText("Top Doctors to Book")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /bob jones/i }),
    ).not.toBeInTheDocument();
  });
});
