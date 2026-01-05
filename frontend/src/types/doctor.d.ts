import type { Speciality } from "./speciality";
import type { User } from "./user";
import type { Hospital } from "./hospital";

export interface Doctor {
  id: number; 
  user: User;
  firstName: string;
  lastName: string;
  speciality: number | Speciality;
  specialityName: string;
  education: string;
  yearsOfExperience: number;
  about: string;
  fees: number | string;
  addressLine1: string;
  addressLine2: string;
  city: string;
  state: string;
  zipCode: string;
  licenseNumber: string;
  certifications: string;
  primaryHospital: number | Hospital | null;  
  hospitals: number[] | Hospital[] | null;
  isRemoved: boolean;
  removedAt: string | null; 
}

export interface DoctorCtx {
  doctors: Doctor[] | null;
  loading: boolean;
  error: string | null;
  getDoctors: () => Promise<Doctor[]>;
}
