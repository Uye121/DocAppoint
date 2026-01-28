import { describe, it, expect, beforeEach } from "vitest";
import { mock } from "../../../test/server";
import {
  scheduleAppointment,
  getSlotsByRange,
  getProviderAppointments,
  getPatientAppointments,
  updateAppointmentStatus,
} from "../appointment";
import type { AppointmentListItem } from "../../types/appointment";

const SLOTS = {
  "2026-01-21": [
    {
      id: "1",
      hospitalId: 1,
      hospitalName: "General Hospital",
      hospitalTimezone: "utc",
      start: "2026-01-21T21:30:00Z",
      end: "2026-01-21T22:00:00Z",
      status: "FREE",
    },
  ],
};
const APPT: AppointmentListItem = {
  id: "a1",
  patientId: "1",
  providerId: "2",
  patientName: "a",
  providerName: "b",
  providerImage: "",
  appointmentStartDatetimeUtc: "",
  appointmentEndDatetimeUtc: "",
  hospital: {
    id: 1,
    name: "General Hospital",
    address: "123 Main St.",
    timezone: "utc",
  },
  reason: "test",
  status: "REQUESTED",
};

describe("appointment API", () => {
  beforeEach(() => mock.reset());

  it("scheduleAppointment POST /appointment/ with payload", async () => {
    const payload = {
      patient: "1",
      provider: "2",
      appointmentStartDatetimeUtc: "2026-01-21T21:30:00Z",
      appointmentEndDatetimeUtc: "2026-01-21T22:00:00Z",
      location: "1",
      reason: "test",
    };
    mock.onPost("/appointment/").reply(200, payload);
    const res = await scheduleAppointment(payload);
    expect(res).toEqual(payload);
  });

  it("getSlotsByRange builds correct query string", async () => {
    const provider = "2";
    const start = "2026-01-21";
    const end = "2026-01-21";

    mock
      .onGet(
        `/slot/range/?provider=${provider}&start_date=${start}&end_date=${end}`,
      )
      .reply(200, SLOTS);
    const res = await getSlotsByRange({
      providerId: "2",
      startDate: "2026-01-21",
      endDate: "2026-01-21",
    });
    expect(res).toEqual(SLOTS);
  });

  it("getProviderAppointments adds provider query", async () => {
    mock.onGet("/appointment/?provider=2").reply(200, [APPT]);
    const res = await getProviderAppointments("2");
    expect(res).toEqual([APPT]);
  });

  it("getPatientAppointments adds patient query", async () => {
    mock.onGet("/appointment/?patient=1").reply(200, [APPT]);
    const res = await getPatientAppointments("1");
    expect(res).toEqual([APPT]);
  });

  it("updateAppointmentStatus POST /appointment/:id/set-status/", async () => {
    mock.onPost("/appointment/a1/set-status/").reply(200, { ok: true });
    const res = await updateAppointmentStatus("a1", "CANCELLED");
    expect(res).toEqual({ ok: true });
  });
});
