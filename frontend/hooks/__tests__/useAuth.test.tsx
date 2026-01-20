import { describe, it, expect } from "vitest";
import { AuthContext } from "../../src/context";
import { useAuth } from "../useAuth";
import { renderHookInProvider } from "../../test/utils";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthContext.Provider
    value={{
      user: { id: 1, email: "a@b.com" },
      loading: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    }}
  >
    {children}
  </AuthContext.Provider>
);
describe("useAuth", () => {
  it("returns context value when inside AuthProvider", () => {
    const value = renderHookInProvider(useAuth, { provider: wrapper });
    expect(value).toHaveProperty("user.email", "a@b.com");
  });
  it("throws when used outside AuthProvider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {}); // suppress error log
    expect(() =>
      renderHookInProvider(useAuth, {
        provider: ({ children }) => <>{children}</>,
      }),
    ).toThrow(/useAuth must be used inside AuthProvider/);
    spy.mockRestore();
  });
});
