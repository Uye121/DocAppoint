import { describe, it, expect, vi } from "vitest";
import { apiClient } from "../client";

const createFetchMock = (status: number, data: unknown) => () =>
  Promise.resolve({
    status,
    headers: new Headers(),
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as Response);

describe("apiClient (fetch wrapper)", () => {
  it("get builds correct URL and returns json", async () => {
    global.fetch = vi.fn(createFetchMock(200, { ok: true }));

    const res = await apiClient.get("dummy");
    expect(res).toEqual({ ok: true });
  });

  it("post sends JSON body and returns json", async () => {
    const body = { name: "test" };
    global.fetch = vi.fn(createFetchMock(201, { id: 1 }));

    const res = await apiClient.post("users", body);
    expect(res).toEqual({ id: 1 });
  });
});
