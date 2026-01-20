import { describe, it, expect } from "vitest";
import { mock } from "../../../test/server";
import { getSpecialities } from "../speciality";
import type { Speciality } from "../../types/speciality";

const SPEC: Speciality = {
  id: 1,
  name: "neurologist",
  image: "",
};

describe("doctor API", () => {
  it("getSpecialities GET /speciality/", async () => {
    mock.onGet("/speciality/").reply(200, [SPEC]);
    const res = await getSpecialities();
    expect(res).toEqual([SPEC]);
  });
});
