import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider } from "../../src/context";
import { VerifyEmail, Login } from "../../src/pages";
import { mock } from "../server";

describe("Email Verification Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  const createWrapper = (initialEntry: string) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    return function Wrapper() {
      return (
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={[initialEntry]}>
            <AuthProvider>
              <Routes>
                <Route path="/verify-email" element={<VerifyEmail />} />
                <Route path="/login" element={<Login />} />
              </Routes>
            </AuthProvider>
          </MemoryRouter>
        </QueryClientProvider>
      );
    };
  };

  it("should successfully verify email with valid token", async () => {
    mock
      .onGet("/auth/verify/", { params: { token: "valid-token" } })
      .reply(200, {
        detail: "Email verified successfully",
      });

    render(<VerifyEmail />, {
      wrapper: createWrapper("/verify-email?token=valid-token"),
    });

    // Verify loading state
    expect(screen.getByText(/verifying your email/i)).toBeInTheDocument();

    // Verify success message
    await waitFor(() => {
      expect(screen.getByText(/email confirmed/i)).toBeInTheDocument();
    });

    // Click through to login
    await user.click(screen.getByRole("button", { name: /go to login/i }));

    // Should navigate to login
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });
  });

  it("should show error for invalid token", async () => {
    // Mock failed verification
    mock
      .onGet("/auth/verify/", { params: { token: "invalid-token" } })
      .reply(400, {
        detail: "Invalid token",
      });

    render(<VerifyEmail />, {
      wrapper: createWrapper("/verify-email?token=invalid-token"),
    });

    // Verify loading state
    expect(screen.getByText(/verifying your email/i)).toBeInTheDocument();

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/invalid or expired link/i)).toBeInTheDocument();
    });
  });

  it("should show error when no token is provided", async () => {
    render(<VerifyEmail />, {
      wrapper: createWrapper("/verify-email"),
    });

    await waitFor(() => {
      expect(screen.getByText(/invalid or expired link/i)).toBeInTheDocument();
    });
  });

  it("should allow resending verification email", async () => {
    // Mock failed verification first
    mock
      .onGet("/auth/verify/", { params: { token: "expired-token" } })
      .reply(400, {
        detail: "Invalid token",
      });

    // Mock resend endpoint
    mock.onPost("http://localhost:8000/api/auth/resend-verify/").reply(200, {
      detail: "Verification email sent",
    });

    render(<VerifyEmail />, {
      wrapper: createWrapper("/verify-email?token=expired-token"),
    });

    await waitFor(() => {
      expect(screen.getByText(/invalid or expired link/i)).toBeInTheDocument();
    });

    // Enter email for resend
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, "test@example.com");

    // Click resend button
    await user.click(
      screen.getByRole("button", { name: /resend verification email/i }),
    );

    // Verify API was called
    expect(mock.history.post).toHaveLength(1);
    expect(JSON.parse(mock.history.post[0].data)).toEqual({
      email: "test@example.com",
    });
  });
});
