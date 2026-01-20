import React from "react";
import { describe, it, expect } from "vitest";
import { SpecialityContext } from "../../src/context";
import { useSpeciality } from "../useSpeciality";
import { renderHookInProvider } from "../../test/utils";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SpecialityContext.Provider
    value={{
      specialities: [
        {
          id: 1,
          name: "Neurologist",
          image: "img.png",
        },
      ],
      loading: false,
      error: null,
      getSpecialities: vi.fn(),
    }}
  >
    {children}
  </SpecialityContext.Provider>
);
describe("useSpeciality", () => {
  it("returns context value when inside SpecialitiesProvider", () => {
    const value = renderHookInProvider(useSpeciality, { provider: wrapper });
    expect(value).toHaveProperty("specialities");
    expect(value.specialities).toHaveLength(1);
    expect(value.specialities[0]).toHaveProperty("id");
    expect(value.specialities[0].name).toBe("Neurologist");
  });
  it("throws when used outside SpecialitiesProvider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() =>
      renderHookInProvider(useSpeciality, {
        provider: ({ children }) => <>{children}</>,
      }),
    ).toThrow(/useSpecialties must be used inside SpecialitiesProvider/);
    spy.mockRestore();
  });
});
