import { api } from "./axios";
import type { Speciality } from "../types/speciality";

export const getSpecialities = () =>
  api.get<Speciality[]>("/speciality/").then((res) => res.data);