import type { Doctor } from "./doctor";
import type { Hospital } from "./hospital";
import type { User } from "./user";

export interface Slot {
  id: string;
  provider: Doctor;
  hospital: Hospital;
  start: string;
  end: string;
  status: "FREE" | "BOOKED" | "BLOCKED" | "UNAVAILABLE";
  duration?: number;
};

export interface AppointmentListItem {
  id: string;
  patient: User;
  provider: Doctor;
  appointmentStartDatetimeUtc: string;
  appointmentEndDatetimeUtc: string;
  location: string;
  status: "REQUESTED" | "CONFIRMED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED";
};

export interface Appointment extends AppointmentListItem {
  reason: string;
  createdAt: string;
  updatedAt: string;
}
