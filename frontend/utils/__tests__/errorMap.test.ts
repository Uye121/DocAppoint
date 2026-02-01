import { describe, it, expect } from "vitest";
import type { AxiosError } from "axios";

import { getErrorMessage } from "../errorMap";

const mockAxiosError = <T = unknown>(data?: T, status = 400): AxiosError<T> =>
  ({
    isAxiosError: true,
    response: { status, data },
    message: "Network Error",
  }) as AxiosError<T>;

describe("getErrorMessage", () => {
  it("returns Axios response detail when present", () => {
    const msg = getErrorMessage(mockAxiosError({ detail: "Invalid email" }));
    expect(msg).toBe("Invalid email");
  });

  it("returns Axios response message when detail missing", () => {
    const msg = getErrorMessage(mockAxiosError({ message: "Bad Request" }));
    expect(msg).toBe("Bad Request");
  });

  it("returns Axios response error when message & detail missing", () => {
    const msg = getErrorMessage(mockAxiosError({ error: "Server fault" }));
    expect(msg).toBe("Server fault");
  });

  it("falls back to Axios message when no response data", () => {
    const err = mockAxiosError(undefined);
    expect(getErrorMessage(err)).toBe("Network Error");
  });

  it("falls back to status text when no message either", () => {
    const err = { ...mockAxiosError(), message: "" };
    expect(getErrorMessage(err)).toBe("Request failed with status 400");
  });

  it("returns Error.message for plain Error", () => {
    expect(getErrorMessage(new Error("Custom error"))).toBe("Custom error");
  });

  it("returns the string itself for string errors", () => {
    expect(getErrorMessage("string error")).toBe("string error");
  });

  it("returns object.message for plain object with message", () => {
    expect(getErrorMessage({ message: "Obj msg" })).toBe("Obj msg");
  });

  it("returns default message for unknown types", () => {
    expect(getErrorMessage(42, "Default")).toBe("Default");
    expect(getErrorMessage(null)).toBe("An unexpected error occurred");
  });
});
