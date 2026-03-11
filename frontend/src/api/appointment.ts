import { api } from "./axios";
import type {
  AppointmentListItem,
  AppointmentPayload,
  Slot,
  SlotRangePayload,
  AppointmentUpdateResponse,
} from "../types/appointment";

export const scheduleAppointment = (payload: AppointmentPayload) =>
  api
    .post<AppointmentPayload>("/appointment/", payload)
    .then((res) => res.data);

export const getSlotsByRange = (payload: SlotRangePayload) =>
  api
    .get<
      Record<string, Slot[]>
    >("/slot/range/", { params: { provider: payload.providerId, start_date: payload.startDate, end_date: payload.endDate } })
    .then((res) => res.data);

export const getProviderAppointments = async (providerId: string) =>
  api
    .get<
      AppointmentListItem[]
    >("/appointment/", { params: { provider: providerId } })
    .then((res) => res.data);

export const getPatientAppointments = async (patientId: string) => {
  const params = new URLSearchParams();
  params.set("patient", patientId);

  return api
    .get<AppointmentListItem[]>("/appointment/", {
      params: { patient: patientId },
    })
    .then((res) => res.data);
};

export const updateAppointmentStatus = async (id: string, status: string) =>
  api
    .post<AppointmentUpdateResponse>(`/appointment/${id}/set-status/`, {
      status,
    })
    .then((res) => res.data);
