import { api } from "./axios";
import type { AppointmentListItem, Appointment } from "../types/appointment";

export const getAppointments = () =>
  api.get<AppointmentListItem[]>("/appointment").then((res) => res.data);

export const getAppointmentById = (id: string) =>
  api.get<Appointment>(`/appointment/${id}`).then((res) => res.data);
