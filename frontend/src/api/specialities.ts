import { api } from "./axios";
import type { Speciality } from "../types/specialities";

export const getSpecialities = () =>
  api.get<Speciality[]>("/speciality/").then((res) => res.data);