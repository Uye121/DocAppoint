import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Signup from "../Signup";

// Mock dependencies
vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../../utils/errorMap", () => ({
  formatErrors: vi.fn((data) => JSON.stringify(data)),
}));

vi.mock("axios", async () => ({
  ...(await vi.importActual("axios")),
  isAxiosError: vi.fn(),
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter initialEntries={["/signup"]}>
    <Routes>
      <Route path="/signup" element={children} />
      <Route
        path="/login"
        element={<div data-testid="login-page">Login</div>}
      />
      <Route
        path="/verify"
        element={<div data-testid="verify-page">Verify Email</div>}
      />
    </Routes>
  </MemoryRouter>
);

import { useAuth } from "../../../hooks/useAuth";
import { isAxiosError } from "axios";
import { formatErrors } from "../../../utils/errorMap";

describe("Signup page", () => {
  const mockSignup = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      signup: mockSignup,
      user: null,
      loading: false,
    });
  });

  it("renders signup form with all fields", () => {
    render(<Signup />, { wrapper: TestWrapper });

    expect(
      screen.getByRole("heading", { name: /create account/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
  });

  it("updates form state on input change", async () => {
    const user = userEvent.setup();
    render(<Signup />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/username/i), "johndoe");
    await user.type(screen.getByLabelText(/first name/i), "John");
    await user.type(screen.getByLabelText(/last name/i), "Doe");
    await user.type(screen.getByLabelText(/email/i), "john@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    expect(screen.getByLabelText(/username/i)).toHaveValue("johndoe");
    expect(screen.getByLabelText(/first name/i)).toHaveValue("John");
    expect(screen.getByLabelText(/last name/i)).toHaveValue("Doe");
    expect(screen.getByLabelText(/email/i)).toHaveValue("john@example.com");
    expect(screen.getByLabelText(/password/i)).toHaveValue("password123");
  });

  it("submits form and navigates to verify on success", async () => {
    const user = userEvent.setup();
    mockSignup.mockResolvedValue(undefined);

    render(<Signup />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/username/i), "johndoe");
    await user.type(screen.getByLabelText(/first name/i), "John");
    await user.type(screen.getByLabelText(/last name/i), "Doe");
    await user.type(screen.getByLabelText(/email/i), "john@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(mockSignup).toHaveBeenCalledWith({
        username: "johndoe",
        firstName: "John",
        lastName: "Doe",
        email: "john@example.com",
        password: "password123",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("verify-page")).toBeInTheDocument();
    });
  });

  it("displays error message on Axios error with detail", async () => {
    const user = userEvent.setup();

    vi.mocked(isAxiosError).mockReturnValue(true);

    // Mock signup to reject with axios error
    mockSignup.mockRejectedValue({
      isAxiosError: true,
      response: {
        data: { detail: "Email already exists" },
      },
    });

    render(<Signup />, { wrapper: TestWrapper });

    // Fill only required fields for the test
    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "existing@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    // Wait for error to appear - it should be the first element in the form
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByRole("alert")).toHaveTextContent("Email already exists");
  });

  it("displays formatted errors on Axios error without detail", async () => {
    const user = userEvent.setup();

    // Create proper axios error
    const axiosError = {
      isAxiosError: true,
      response: {
        data: { username: ["This field is required"] },
      },
    };

    mockSignup.mockRejectedValue(axiosError);
    vi.mocked(isAxiosError).mockReturnValue(true);

    // Mock formatErrors to return a readable string
    vi.mocked(formatErrors).mockReturnValue("Username: This field is required");

    render(<Signup />, { wrapper: TestWrapper });

    // MUST fill all required fields to bypass HTML5 validation
    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Username: This field is required",
    );
  });

  it("displays error message on generic Error", async () => {
    const user = userEvent.setup();

    // Mock isAxiosError to return false for generic Error
    vi.mocked(isAxiosError).mockReturnValue(false);

    mockSignup.mockRejectedValue(new Error("Network error"));

    render(<Signup />, { wrapper: TestWrapper });

    // FILL ALL REQUIRED FIELDS FIRST
    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByRole("alert")).toHaveTextContent("Network error");
  });

  it("disables submit button while loading", async () => {
    const user = userEvent.setup();

    // Create a promise that never resolves to keep loading state
    let resolvePromise: () => void;
    const neverResolvingPromise = new Promise<void>((resolve) => {
      resolvePromise = resolve;
    });

    mockSignup.mockImplementation(() => neverResolvingPromise);

    render(<Signup />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    await user.click(submitButton);

    expect(submitButton).toBeDisabled();

    // Resolve the promise to avoid test hanging
    resolvePromise!();
  });

  it("navigates to login page when clicking 'here' link", async () => {
    const user = userEvent.setup();
    render(<Signup />, { wrapper: TestWrapper });

    await user.click(screen.getByText("here"));

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  it("shows error alert when error state is set", () => {
    render(<Signup />, { wrapper: TestWrapper });

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
