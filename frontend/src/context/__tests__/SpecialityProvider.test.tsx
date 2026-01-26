import { useContext } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { SpecialitiesProvider } from "../SpecialityProvider";
import { SpecialityContext } from "../SpecialityContext";
import * as specialityApi from "../../api/speciality";

vi.mock("../../api/speciality", () => ({
  getSpecialities: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <SpecialitiesProvider>{children}</SpecialitiesProvider>
);

describe("SpecialitiesProvider", () => {
  it("exposes loading=true + empty array initially", () => {
    const { result } = renderHook(() => useContext(SpecialityContext)!, {
      wrapper,
    });
    expect(result.current.loading).toBe(true);
    expect(result.current.specialities).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("populates specialities after fetch", async () => {
    const list = [{ id: 1, name: "Cardiology", image: "" }];
    vi.mocked(specialityApi.getSpecialities).mockResolvedValue(list);

    const { result } = renderHook(() => useContext(SpecialityContext)!, {
      wrapper,
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.specialities).toEqual(list);
  });

  it("sets error on fetch failure", async () => {
    vi.mocked(specialityApi.getSpecialities).mockRejectedValue(
      new Error("network"),
    );

    const { result } = renderHook(() => useContext(SpecialityContext)!, {
      wrapper,
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("network");
  });
});
