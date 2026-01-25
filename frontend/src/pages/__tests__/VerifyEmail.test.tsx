import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import VerifyEmail from "../VerifyEmail";

vi.mock("../../api/auth", () => ({
  verifyEmail: vi.fn(),
  resendVerify: vi.fn(),
}));

import { verifyEmail, resendVerify } from "../../api/auth";

const createTestWrapper = (initialRoute: string) => {
  return function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/verify-email" element={children} />
          <Route
            path="/login"
            element={<div data-testid="login-page">Login</div>}
          />
          <Route
            path="/verify"
            element={<div data-testid="verify-page">Check Email</div>}
          />
        </Routes>
      </MemoryRouter>
    );
  };
};

describe("VerifyEmail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    vi.mocked(verifyEmail).mockImplementation(() => new Promise(() => {}));

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email?token=valid-token"),
    });

    expect(screen.getByText(/verifying your email/i)).toBeInTheDocument();
  });

  it("shows success state when verification succeeds", async () => {
    vi.mocked(verifyEmail).mockResolvedValue(undefined);

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email?token=valid-token"),
    });

    await waitFor(() => {
      expect(screen.getByText(/email confirmed/i)).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /go to login/i }),
    ).toBeInTheDocument();
  });

  it("navigates to login from success state", async () => {
    const user = userEvent.setup();
    vi.mocked(verifyEmail).mockResolvedValue(undefined);

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email?token=valid-token"),
    });

    await waitFor(() => {
      expect(screen.getByText(/email confirmed/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /go to login/i }));

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  it("shows failure state when no token in URL", async () => {
    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email"),
    });

    await waitFor(() => {
      expect(screen.getByText(/invalid or expired link/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /resend verification email/i }),
    ).toBeInTheDocument();
  });

  it("shows failure state when verification API fails", async () => {
    vi.mocked(verifyEmail).mockRejectedValue(new Error("Invalid token"));

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email?token=invalid-token"),
    });

    await waitFor(() => {
      expect(screen.getByText(/invalid or expired link/i)).toBeInTheDocument();
    });
  });

  it("updates email input on change", async () => {
    const user = userEvent.setup();

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email"),
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, "test@example.com");

    expect(emailInput).toHaveValue("test@example.com");
  });

  it("resends verification email and navigates to verify page", async () => {
    const user = userEvent.setup();
    vi.mocked(resendVerify).mockResolvedValue(undefined);

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email"),
    });

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(
      screen.getByRole("button", { name: /resend verification email/i }),
    );

    await waitFor(() => {
      expect(vi.mocked(resendVerify)).toHaveBeenCalledWith({
        email: "test@example.com",
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId("verify-page")).toBeInTheDocument();
    });
  });

  it("navigates to login from failure state", async () => {
    const user = userEvent.setup();

    render(<VerifyEmail />, {
      wrapper: createTestWrapper("/verify-email"),
    });

    await waitFor(() => {
      expect(screen.getByText(/invalid or expired link/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /^go to login$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });
});
