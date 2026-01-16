import type { Doctor } from "./doctor";
import type { User } from "./user";

export interface Slot {
  id: string;
  hospitalId: int;
  hospitalName: string;
  hospitalTimezone: string;
  start: string;
  end: string;
  status: "FREE" | "BOOKED" | "BLOCKED" | "UNAVAILABLE";
}

export interface SlotRangePayload {
  providerId: string;
  startDate?: string;
  endDate?: string;
}

export interface AppointmentListItem {
  id: string;
  patient: User;
  provider: Doctor;
  appointmentStartDatetimeUtc: string;
  appointmentEndDatetimeUtc: string;
  location: string;
  status: "REQUESTED" | "CONFIRMED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED";
}

export interface Appointment extends AppointmentListItem {
  reason: string;
  createdAt: string;
  updatedAt: string;
}

export interface AppointmentPayload {
  patient?: User;
  provider: string;
  appointmentStartDatetimeUtc: string;
  appointmentEndDatetimeUtc: string;
  location: string;
  reason: string;
}
