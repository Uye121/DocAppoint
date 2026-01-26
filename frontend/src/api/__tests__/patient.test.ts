import { describe, it, expect } from "vitest";
import { mock } from "../../../test/server";
import { onboard } from "../patient";

describe("patient API", () => {
  it("onboard POST /patient/onboard/", async () => {
    const payload = { bloodType: "A" };
    mock.onPost("/patient/onboard/").reply(201, { id: 1, ...payload });

    const res = await onboard(payload);
    expect(res).toMatchObject(payload);
  });
});
