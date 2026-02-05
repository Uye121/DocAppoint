import { api } from "./axios";

import type { Patient, PatientDetail } from "../types/patient";

export const onboard = (payload: Patient) =>
  api.post<Patient>("/patient/onboard/", payload).then((res) => res.data);

export const getPatientInfo = () =>
  api.get<PatientDetail>("/patient/me").then((res) => res.data);

export const updatePatientInfo = (id: string, payload: PatientDetail) =>
  api.patch<PatientDetail>(`/patient/${id}/`, payload).then((res) => res.data);
