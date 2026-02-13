export interface BaseMedicalRecord {
  id: number;
  patient: string;
  providerId: string;
  hospital: number;
  diagnosis: string;
  notes: string;
  prescriptions: string;
}

export interface MedicalRecordItem {
  id: string;
  patientId: string;
  patientName: string;
  providerId: string;
  providerName: string;
  hospitalName: string;
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

export interface MedicalRecordDetail {
  id: number;
  patientDetails: PatientDetails;
  providerDetails: DoctorDetails;
  hospitalDetails: HospitalDetails;
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

export interface CreateMedicalRecord {
  patient: string;
  hospital: number;
  diagnosis: string;
  notes: string;
  prescriptions: string;
}

export interface UpdateMedicalRecord {
  hospital?: number;
  diagnosis?: string;
  notes?: string;
  prescriptions?: string;
}
