import type { User } from "./user";

export interface Patient {
  bloodType?: string;
  allergies?: string;
  chronicConditions?: string;
  currentMedications?: string;
  insurance?: string;
  weight?: number;
  height?: number;
}

export interface PatientDetail {
  user?: User;
  bloodType?: string;
  allergies?: string;
  chronicConditions?: string;
  currentMedications?: string;
  insurance?: string;
  weight?: number;
  height?: number;
}
