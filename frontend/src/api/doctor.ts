import { api } from "./axios";
import type { Doctor } from "../types/doctor";

export const getDoctors = () =>
  api.get<Doctor[]>("/provider/").then((res) => res.data);