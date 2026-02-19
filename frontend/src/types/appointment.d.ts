import type { HospitalTiny } from "./hospital";

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
  patientId: string;
  providerId: string;
  patientName: string;
  providerName: string;
  providerImage: string | null;
  appointmentStartDatetimeUtc: string;
  appointmentEndDatetimeUtc: string;
  hospital: HospitalTiny;
  reason: string;
  status: "REQUESTED" | "CONFIRMED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED";
}

export interface Appointment extends AppointmentListItem {
  reason: string;
  createdAt: string;
  updatedAt: string;
}

export interface AppointmentPayload {
  patient?: string;
  provider: string;
  appointmentStartDatetimeUtc: string;
  appointmentEndDatetimeUtc: string;
  location: string;
  reason: string;
}

export interface AppointmentUpdateResponse {
  detail: string;
}
