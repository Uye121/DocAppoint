export interface BaseMedicalRecord {
  id: number;
  patientId: string;
  providerId: string;
  hospitalId: number;
  appointmentId: string;
  diagnosis: string;
  notes: string;
  prescriptions: string;
  createdAt: string;
  upddatedAt: string;
}

export interface MedicalRecordItem {
  id: string;
  patientId: string;
  patientName: string;
  providerId: string;
  providerName: string;
  hospitalId: string;
  hospitalName: string;
  appointmentId: string;
  diagnosis: string;
  createdAt: string;
  updatedAt: string;
}

export interface PatientDetails {
  id: string;
  bloodType: string | null;
  allergies: string | null;
  chronicConditions: string | null;
  currentMedications: string | null;
  insurance: string | null;
  weight: number | null;
  height: number | null;
  fullName: string;
  dateOfBirth: string | null;
  image: string | null;
}

export interface DoctorDetails {
  id: string;
  specialityName: string | null;
  licenseNumber: string;
  fullName: string;
}

export interface HospitalDetails {
  id: number;
  name: string;
  phoneNumber: string;
  timezone: string;
}

export interface AppointmentDetails {
  startDatetimeUtc: string;
  endDatetimeUtc: string;
  reason: string;
  status: "REQUESTED" | "CONFIRMED" | "COMPLETED" | "CANCELLED" | "RESCHEDULED";
}

export interface MedicalRecordDetail {
  id: number;
  patientDetails: PatientDetails;
  providerDetails: DoctorDetails;
  hospitalDetails: HospitalDetails;
  appointmentDetails: AppointmentDetails;
  diagnosis: string;
  notes: string;
  prescriptions: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  createdByName: string;
  updatedBy: string;
  updatedByName: string;
  isRemoved: boolean;
  removedAt: string;
}

export interface MedicalRecordPayload {
  patientId: string;
  hospitalId: number;
  appointmentId: string;
  diagnosis: string;
  notes: string;
  prescriptions: string;
}

export interface UpdateMedicalRecordResponse {
  patientId: string;
  hospitalId: number;
  appointmentId: string;
  diagnosis: string;
  notes: string;
  prescriptions: string;
}
