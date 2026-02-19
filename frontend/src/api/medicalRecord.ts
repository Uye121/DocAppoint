import { api } from "./axios";

import type {
  MedicalRecordDetail,
  MedicalRecordPayload,
  UpdateMedicalRecordResponse,
} from "../types/medicalRecord";

export const getMedicalRecordByAppointment = (id: string) =>
  api
    .get<MedicalRecordDetail[]>("/medical-record/", {
      params: { appointment: id },
    })
    .then((res) => (res.data && res.data.length > 0 ? res.data[0] : null)); // Filtering returns list even though the mapping is one-to-one

export const createMedicalRecord = (payload: MedicalRecordPayload) =>
  api
    .post<MedicalRecordDetail>("/medical-record/", payload)
    .then((res) => res.data);

export const updateMedicalRecord = (
  id: number,
  payload: Partial<MedicalRecordPayload>,
) =>
  api
    .patch<UpdateMedicalRecordResponse>(`/medical-record/${id}/`, payload)
    .then((res) => res.data);
