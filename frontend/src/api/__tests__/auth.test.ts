import { describe, it, expect, vi, beforeEach } from "vitest";
import { mock } from "../../../test/server";
import * as auth from "../auth";

describe("auth API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mock.reset();
  });

  it("login POST /auth/login/ and returns user + tokens", async () => {
    const payload = { email: "a@b.com", password: "secret" };
    const reply = {
      user: { id: 1, email: "a@b.com" },
      access: "acc",
      refresh: "ref",
    };
    mock.onPost("/auth/login/").reply(200, reply);
    const res = await auth.login(payload);
    expect(res).toEqual(reply);
  });

  it("signup POST /users/", async () => {
    const payload = { email: "a@b.com", password: "secret" };
    mock.onPost("/users/").reply(201, { id: 1 });
    const res = await auth.signup(payload);
    expect(res).toEqual({ id: 1 });
  });

  it("logout POST /auth/logout/ with refresh token from localStorage", async () => {
    localStorage.setItem("refresh", "ref");
    mock.onPost("/auth/logout/").reply(200, { ok: true });
    const res = await auth.logout();
    expect(res).toEqual({ ok: true });
  });

  it("logout resolves immediately when no refresh token", async () => {
    const res = await auth.logout();
    expect(res).toBeUndefined();
  });
});
