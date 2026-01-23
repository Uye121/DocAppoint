import React, { useContext } from "react";
import { renderHook, waitFor, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { vi } from "vitest";
import { AuthProvider } from "../AuthProvider";
import { AuthContext } from "../AuthContext";
import * as authApi from "../../api/auth";

vi.mock("../../api/auth", () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  signup: vi.fn(),
  logout: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter>
    <AuthProvider>{children}</AuthProvider>
  </MemoryRouter>
);

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });
  afterEach(() => localStorage.clear());

  it("exposes default state while bootstrapping", () => {
    vi.mocked(authApi.getMe).mockImplementation(() => new Promise(() => {}));
    localStorage.setItem("access", "test-token");
    const { result } = renderHook(() => useContext(AuthContext), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(true);
  });

  it("sets user when access token exists and /me succeeds", async () => {
    const fakeUser = { id: 1, email: "a@b.com" };
    vi.mocked(authApi.getMe).mockResolvedValue(fakeUser);
    localStorage.setItem("access", "tok");

    const { result } = renderHook(() => useContext(AuthContext), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toEqual(fakeUser);
  });

  it("clears token and stays logged-out when /me fails", async () => {
    vi.mocked(authApi.getMe).mockRejectedValue(new Error("401"));
    localStorage.setItem("access", "bad");

    const { result } = renderHook(() => useContext(AuthContext), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("access")).toBeNull();
  });

  it("login flow stores tokens and user", async () => {
    const { result } = renderHook(() => useContext(AuthContext), { wrapper });

    const fakeReply = {
      user: { id: 2, email: "a@b.com", userRole: "patient" },
      access: "acc",
      refresh: "ref",
    };
    vi.mocked(authApi.login).mockResolvedValue(fakeReply);

    await act(async () => {
      await result.current.login({ email: "u", password: "p" });
    });

    expect(authApi.login).toHaveBeenCalledWith({ email: "u", password: "p" });
    expect(localStorage.getItem("access")).toBe("acc");
    expect(localStorage.getItem("refresh")).toBe("ref");
    expect(result.current.user).toEqual(fakeReply.user);
  });
});
