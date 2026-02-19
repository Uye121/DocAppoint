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

export const getSlotsByRange = (payload: SlotRangePayload) => {
  const params = new URLSearchParams();
  params.set("provider", payload.providerId);
  if (payload.startDate && payload.endDate) {
    params.set("start_date", payload.startDate);
    params.set("end_date", payload.endDate);
  }

  return api
    .get<Record<string, Slot[]>>(`/slot/range/?${params.toString()}`)
    .then((res) => res.data);
};

export const getProviderAppointments = async (providerId: string) =>
  api
    .get<AppointmentListItem[]>(`/appointment/?provider=${providerId}`)
    .then((res) => res.data);

export const getPatientAppointments = async (patientId: string) =>
  api
    .get<AppointmentListItem[]>(`/appointment/?patient=${patientId}`)
    .then((res) => res.data);

export const updateAppointmentStatus = async (id: string, status: string) =>
  api
    .post<AppointmentUpdateResponse>(`/appointment/${id}/set-status/`, {
      status,
    })
    .then((res) => res.data);
