export interface MedicalRecord {
  id: number;
  patient: string;
  healthcareProvider: string;
  diagnosis: string;
  notes: string;
  prescriptions: string;
  isRemoved: boolean;
}
