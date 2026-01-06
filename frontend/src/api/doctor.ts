import { api } from "./axios";
import type { DoctorListItem, Doctor } from "../types/doctor";

export const getDoctors = () =>
  api.get<DoctorListItem[]>("/provider/").then((res) => res.data);

export const getDoctorById = (id: string) =>
  api.get<Doctor>(`/provider/${id}`).then((res) => res.data);
