import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";

import { mock } from "../../../test/server";
import { api } from "../axios";

// Attach to global axios object to trap the refresh request, which was
// made to a different axios instance in interceptor
const plainMock = new MockAdapter(axios);

describe("axios interceptors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mock.reset();
    delete api.defaults.headers.common["Authorization"];
  });

  it("attaches access token from localStorage to request", async () => {
    localStorage.setItem("access", "acc");
    let header: string | undefined;
    mock.onGet("/foo").reply((config) => {
      header = config.headers?.Authorization as string;
      return [200, {}];
    });
    await api.get("/foo");
    expect(header).toBe("Bearer acc");
  });

  it("retries 401 with refreshed token and replays queued request", async () => {
    localStorage.setItem("access", "acc");
    localStorage.setItem("refresh", "ref");

    /* mock the stand-alone axios call made by the interceptor */
    plainMock
      .onPost("http://localhost:8000/api/auth/token/refresh/")
      .reply(200, { access: "new" });

    mock.onGet("/first").replyOnce(401);
    mock.onGet("/first").reply(200, { ok: true });

    const res = await api.get("/first");
    expect(res.data).toEqual({ ok: true });
    expect(api.defaults.headers.common["Authorization"]).toBe("Bearer new");
    expect(localStorage.getItem("access")).toBe("new");
  });

  it("clears storage and redirects on refresh failure", async () => {
    localStorage.setItem("access", "acc");
    localStorage.setItem("refresh", "bad");
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    plainMock
      .onPost("http://localhost:8000/api/auth/token/refresh/")
      .reply(401, { detail: "Invalid refresh token" });

    mock.onGet("/first").replyOnce(401);

    await expect(api.get("/first")).rejects.toThrow();
    expect(localStorage.length).toBe(0);
    expect(window.location.href).toBe("/login");
  });
});
