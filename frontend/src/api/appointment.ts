import { api } from "./axios";
import type {
  AppointmentListItem,
  Appointment,
  Slot,
  SlotRangePayload
} from "../types/appointment";

export const getAppointments = () =>
  api.get<AppointmentListItem[]>("/appointment").then((res) => res.data);

export const getAppointmentById = (id: string) =>
  api.get<Appointment>(`/appointment/${id}`).then((res) => res.data);

export const getSlotsByRange = (payload: SlotRangePayload) => {
  const params = new URLSearchParams();
  params.set("provider", payload.providerId);
  if (payload.startDate && payload.endDate) {
    params.set("start_date", payload.startDate);
    params.set("end_date", payload.endDate);
  }
  return api
    .get<Slot>(`/slot/range/?${params.toString()}`)
    .then((res) => res.data);
}
  

