import type { Speciality } from "./speciality";
import type { User } from "./user";
import type { Hospital } from "./hospital";

export interface DoctorListItem {
  id: number;
  speciality: number | Speciality;
  specialityName: string;
  firstName: string;
  lastName: string;
  image: string;
}

export interface Doctor extends DoctorListItem {
  user: User;
  education: string;
  yearsOfExperience: number;
  about: string;
  fees: string;
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
  doctors: DoctorListItem[] | null;
  loading: boolean;
  error: string | null;
  getDoctors: () => Promise<DoctorListItem[]>;
}
