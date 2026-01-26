import { useContext } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { DoctorProvider } from "../DoctorProvider";
import { DoctorContext } from "../DoctorContext";
import * as doctorApi from "../../api/doctor";

vi.mock("../../api/doctor", () => ({
  getDoctors: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <DoctorProvider>{children}</DoctorProvider>
);

describe("DoctorProvider", () => {
  it("exposes loading=true + empty doctors initially", () => {
    const { result } = renderHook(() => useContext(DoctorContext), { wrapper });
    expect(result.current.loading).toBe(true);
    expect(result.current.doctors).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("fills doctors and stops loading after successful fetch", async () => {
    const list = [
      {
        id: 1,
        speciality: 1,
        specialityName: "Neurology",
        firstName: "A",
        lastName: "B",
        image: "",
      },
    ];
    vi.mocked(doctorApi.getDoctors).mockResolvedValue(list);

    const { result } = renderHook(() => useContext(DoctorContext)!, {
      wrapper,
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.doctors).toEqual(list);
    expect(result.current.error).toBeNull();
  });

  it("sets error when fetch fails", async () => {
    vi.mocked(doctorApi.getDoctors).mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => useContext(DoctorContext)!, {
      wrapper,
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.doctors).toEqual([]);
    expect(result.current.error).toBe("boom");
  });

  it("getDoctors() refreshes list and returns it", async () => {
    const list = [
      {
        id: 1,
        speciality: 1,
        specialityName: "Neurology",
        firstName: "A",
        lastName: "B",
        image: "",
      },
    ];
    vi.mocked(doctorApi.getDoctors)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(list);

    const { result } = renderHook(() => useContext(DoctorContext)!, {
      wrapper,
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
    const returned = await result.current.getDoctors();

    await waitFor(() => {
      expect(returned).toEqual(list);
      expect(result.current.doctors).toEqual(list);
    });
  });
});
