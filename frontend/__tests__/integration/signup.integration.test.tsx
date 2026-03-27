import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { toast } from "react-toastify";

import { AuthProvider } from "../../src/context";
import { Signup, Verify } from "../../src/pages";
import { mock } from "../server";

describe("Signup Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    return function Wrapper() {
      return (
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={["/signup"]}>
            <AuthProvider>
              <Routes>
                <Route path="/signup" element={<Signup />} />
                <Route path="/verify" element={<Verify />} />
              </Routes>
            </AuthProvider>
          </MemoryRouter>
        </QueryClientProvider>
      );
    };
  };

  it("should successfully sign up a new user", async () => {
    mock.onPost("http://localhost:8000/api/users/").reply(201, {
      id: "123",
      email: "test@example.com",
    });

    render(<Signup />, { wrapper: createWrapper() });

    // Fill signup form
    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "Password123!");

    // Submit form
    await user.click(screen.getByRole("button", { name: /create account/i }));

    // Verify redirect to verify page
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /verify email/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/please check email to verify email/i),
      ).toBeInTheDocument();
    });
  });

  it("should show error when email already exists", async () => {
    mock.onPost("http://localhost:8000/api/users/").reply(400, {
      email: ["User with this email already exists."],
    });

    render(<Signup />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "existing@example.com");
    await user.type(screen.getByLabelText(/password/i), "Password123!");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining("already exists"),
      );
    });

    // Should stay on signup page
    expect(screen.queryByText(/verify email/i)).not.toBeInTheDocument();
  });

  it("should show validation error for invalid email", async () => {
    render(<Signup />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/username/i), "testuser");
    await user.type(screen.getByLabelText(/first name/i), "Test");
    await user.type(screen.getByLabelText(/last name/i), "User");
    await user.type(screen.getByLabelText(/email/i), "invalid-email");
    await user.type(screen.getByLabelText(/password/i), "Password123!");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    // No API call should be made
    expect(mock.history.post.length).toBe(0);
  });
});
