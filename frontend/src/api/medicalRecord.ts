import { api } from "./axios";

import type {
  MedicalRecordItem,
  CreateMedicalRecord,
  MedicalRecordDetail,
} from "../types/medicalRecord";

export const getMedicalRecords = () =>
  api.get<MedicalRecordItem[]>("/medical-record/").then((res) => res.data);

export const createMedicalRecord = (payload: CreateMedicalRecord) =>
  api
    .post<MedicalRecordDetail>("/medical-record/", payload)
    .then((res) => res.data);
