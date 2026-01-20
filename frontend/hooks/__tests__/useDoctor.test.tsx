import React from "react";
import { describe, it, expect } from "vitest";
import { DoctorContext } from "../../src/context";
import { useDoctor } from "../useDoctor";
import { renderHookInProvider } from "../../test/utils";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <DoctorContext.Provider
    value={{
      doctors: [
        {
          id: 1,
          speciality: 1,
          firstName: "Bob",
          lastName: "Nelson",
          image: "img.png",
          specialityName: "",
        },
      ],
      loading: false,
      error: null,
      getDoctors: vi.fn(),
    }}
  >
    {children}
  </DoctorContext.Provider>
);

describe("useDoctor", () => {
  it("returns context value when inside DoctorProvider", () => {
    const value = renderHookInProvider(useDoctor, { provider: wrapper });
    expect(value).toHaveProperty("doctors");
    expect(value.doctors).toHaveLength(1);
    expect(value.doctors[0]).toHaveProperty("id", 1);
    expect(value.doctors[0].firstName).toBe("Bob");
  });

  it("throws when used outside DoctorProvider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() =>
      renderHookInProvider(useDoctor, {
        provider: ({ children }) => <>{children}</>,
      }),
    ).toThrow(/useDoctor must be used inside DoctorProvider/);
    spy.mockRestore();
  });
});
