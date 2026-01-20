import type { User } from "./user";

export interface DoctorListItem {
  id: number;
  speciality: number;
  specialityName: string;
  firstName: string;
  lastName: string;
  image: string;
}

export interface Doctor extends DoctorListItem {
  about: string;
  addressLine1: string;
  addressLine2: string;
  certifications: string;
  city: string;
  education: string;
  fees: string;
  hospitals: number[] | null;
  id: string;
  isRemoved: boolean;
  licenseNumber: string;
  primaryHospital: number | null;
  removedAt: string | null;
  speciality: number | null;
  specialityName: string | null;
  state: string;
  user: User;
  yearsOfExperience: number;
  zipCode: string;
}

export interface DoctorCtx {
  doctors: DoctorListItem[] | null;
  loading: boolean;
  error: string | null;
  getDoctors: () => Promise<DoctorListItem[]>;
}
