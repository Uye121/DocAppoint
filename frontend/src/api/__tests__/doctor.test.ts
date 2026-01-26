import { describe, it, expect } from "vitest";
import { mock } from "../../../test/server";
import { getDoctors, getDoctorById } from "../doctor";
import type { DoctorListItem } from "../../types/doctor";

const DOCITEM: DoctorListItem = {
  id: 1,
  speciality: 1,
  specialityName: "Neurologist",
  firstName: "a",
  lastName: "b",
  image: "",
};

describe("doctor API", () => {
  it("getDoctors GET /provider/", async () => {
    mock.onGet("/provider/").reply(200, [DOCITEM]);
    const res = await getDoctors();
    expect(res).toEqual([DOCITEM]);
  });

  it("getDoctorById GET /provider/:id", async () => {
    mock.onGet("/provider/d1").reply(200, DOCITEM);
    const res = await getDoctorById("d1");
    expect(res).toEqual(DOCITEM);
  });
});
