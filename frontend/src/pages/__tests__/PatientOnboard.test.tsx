import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import PatientOnboard from "../PatientOnboard";

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../api/patient", () => ({
  onboard: vi.fn(),
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter initialEntries={["/onboard"]}>
    <Routes>
      <Route path="/onboard" element={children} />
      <Route path="/" element={<div data-testid="home-page">Home</div>} />
    </Routes>
  </MemoryRouter>
);

import { useAuth } from "../../../hooks/useAuth";
import { onboard } from "../../api/patient";

describe("PatientOnboard", () => {
  const mockRefreshUser = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      refreshUser: mockRefreshUser,
    });
  });

  it("renders onboarding form with all fields", () => {
    render(<PatientOnboard />, { wrapper: TestWrapper });

    expect(
      screen.getByRole("heading", { name: /complete your profile/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/blood type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/insurance/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/weight/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/height/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/allergies/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/chronic conditions/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/current medications/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /save profile/i }),
    ).toBeInTheDocument();
  });

  it("updates text fields on change", async () => {
    const user = userEvent.setup();
    render(<PatientOnboard />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/blood type/i), "O+");
    await user.type(screen.getByLabelText(/insurance/i), "Blue Cross");

    expect(screen.getByLabelText(/blood type/i)).toHaveValue("O+");
    expect(screen.getByLabelText(/insurance/i)).toHaveValue("Blue Cross");
  });

  it("updates number fields and converts to numbers", async () => {
    const user = userEvent.setup();
    render(<PatientOnboard />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/weight/i), "70");
    await user.type(screen.getByLabelText(/height/i), "175");

    expect(screen.getByLabelText(/weight/i)).toHaveValue(70);
    expect(screen.getByLabelText(/height/i)).toHaveValue(175);
  });

  it("updates textarea fields on change", async () => {
    const user = userEvent.setup();
    render(<PatientOnboard />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/allergies/i), "Peanuts, Shellfish");
    await user.type(screen.getByLabelText(/chronic conditions/i), "Asthma");

    expect(screen.getByLabelText(/allergies/i)).toHaveValue(
      "Peanuts, Shellfish",
    );
    expect(screen.getByLabelText(/chronic conditions/i)).toHaveValue("Asthma");
  });

  it("submits form and navigates to home on success", async () => {
    const user = userEvent.setup();
    vi.mocked(onboard).mockResolvedValue(undefined);
    mockRefreshUser.mockResolvedValue(undefined);

    render(<PatientOnboard />, { wrapper: TestWrapper });

    // Fill out form
    await user.type(screen.getByLabelText(/blood type/i), "A+");
    await user.type(screen.getByLabelText(/weight/i), "65");
    await user.type(screen.getByLabelText(/allergies/i), "None");

    await user.click(screen.getByRole("button", { name: /save profile/i }));

    await waitFor(() => {
      expect(onboard).toHaveBeenCalledWith({
        bloodType: "A+",
        weight: 65,
        allergies: "None",
      });
    });

    await waitFor(() => {
      expect(mockRefreshUser).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByTestId("home-page")).toBeInTheDocument();
    });
  });

  it("handles empty number fields by setting undefined", async () => {
    const user = userEvent.setup();
    vi.mocked(onboard).mockResolvedValue(undefined);
    mockRefreshUser.mockResolvedValue(undefined);

    render(<PatientOnboard />, { wrapper: TestWrapper });

    const weightInput = screen.getByLabelText(/weight/i);
    await user.type(weightInput, "70");
    await user.clear(weightInput);

    await user.click(screen.getByRole("button", { name: /save profile/i }));

    await waitFor(() => {
      expect(onboard).toHaveBeenCalledWith(
        expect.objectContaining({
          weight: undefined,
        }),
      );
    });
  });

  it("handles submission error gracefully", async () => {
    const user = userEvent.setup();
    const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    vi.mocked(onboard).mockRejectedValue(new Error("Network error"));

    render(<PatientOnboard />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/blood type/i), "B+");
    await user.click(screen.getByRole("button", { name: /save profile/i }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(expect.any(Error));
    });

    // Should not navigate on error
    expect(
      screen.getByRole("heading", { name: /complete your profile/i }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("home-page")).not.toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it("allows submitting with all fields empty", async () => {
    const user = userEvent.setup();
    vi.mocked(onboard).mockResolvedValue(undefined);
    mockRefreshUser.mockResolvedValue(undefined);

    render(<PatientOnboard />, { wrapper: TestWrapper });

    // Submit without filling any fields
    await user.click(screen.getByRole("button", { name: /save profile/i }));

    await waitFor(() => {
      expect(onboard).toHaveBeenCalledWith({});
    });

    await waitFor(() => {
      expect(screen.getByTestId("home-page")).toBeInTheDocument();
    });
  });
});
