import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Login from "../Login";

vi.mock("../../../hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("axios", async () => ({
  ...(await vi.importActual("axios")),
  isAxiosError: vi.fn(),
}));

vi.mock("../../../utils/errorMap", () => ({
  getErrorMessage: vi.fn((err) => {
    if (err?.isAxiosError) {
      return err.response?.data?.detail || JSON.stringify(err.response?.data);
    }
    return err?.message || String(err);
  }),
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter initialEntries={["/login"]}>
    <Routes>
      <Route path="/login" element={children} />
      <Route path="/" element={<div data-testid="home-page">Home</div>} />
      <Route
        path="/signup"
        element={<div data-testid="signup-page">Signup</div>}
      />
    </Routes>
  </MemoryRouter>
);

import { isAxiosError } from "axios";
import { useAuth } from "../../../hooks/useAuth";

describe("Login page", () => {
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useAuth).mockReturnValue({
      login: mockLogin,
      user: null,
      loading: false,
    });
  });

  it("renders login form with email and password inputs", () => {
    render(<Login />, { wrapper: TestWrapper });

    expect(screen.getByRole("heading", { name: "Login" })).toBeInTheDocument();

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  it("updates form state on input change", async () => {
    const user = userEvent.setup();
    render(<Login />, { wrapper: TestWrapper });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");

    expect(emailInput).toHaveValue("test@example.com");
    expect(passwordInput).toHaveValue("password123");
  });

  it("calls login and navigates to home on successful submit", async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue(undefined);

    render(<Login />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("home-page")).toBeInTheDocument();
    });
  });

  it("displays error message on 400 Axios error with detail", async () => {
    const user = userEvent.setup();
    const axiosError = {
      isAxiosError: true,
      response: {
        status: 400,
        data: { detail: "Invalid credentials" },
      },
    };

    mockLogin.mockRejectedValue(axiosError);
    vi.mocked(isAxiosError).mockReturnValue(true);

    render(<Login />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Invalid credentials",
      );
    });
  });

  it("displays formatted errors on 400 Axios error without detail", async () => {
    const user = userEvent.setup();
    const axiosError = {
      isAxiosError: true,
      response: {
        status: 400,
        data: { email: ["This field is required"] },
      },
    };

    mockLogin.mockRejectedValue(axiosError);
    vi.mocked(isAxiosError).mockReturnValue(true);

    render(<Login />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        JSON.stringify({ email: ["This field is required"] }),
      );
    });
  });

  it("displays error message on generic Error", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error("Network error"));

    render(<Login />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network error");
    });
  });

  it("displays 'Unexpected error' for unknown error types", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue("Unexpected error");

    render(<Login />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Unexpected error");
    });
  });

  it("disables submit button while loading", async () => {
    const user = userEvent.setup();

    // Delay login resolution to test loading state
    mockLogin.mockImplementation(() => new Promise(() => {}));

    render(<Login />, { wrapper: TestWrapper });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    const submitButton = screen.getByRole("button", { name: /login/i });
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
  });

  it("navigates to signup page when clicking 'here' link", async () => {
    const user = userEvent.setup();
    render(<Login />, { wrapper: TestWrapper });

    await user.click(screen.getByText("here"));

    await waitFor(() => {
      expect(screen.getByTestId("signup-page")).toBeInTheDocument();
    });
  });

  it("clears error when user starts typing again", async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error("Invalid credentials"));

    render(<Login />, { wrapper: TestWrapper });

    // Submit to trigger error
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrong");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "newemail@example.com");
  });
});
