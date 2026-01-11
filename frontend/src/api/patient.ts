import { api } from "./axios";

import type { Patient } from "../types/patient";

export const onboard = (payload: Patient) =>
  api.post<Patient>("/patient/onboard/", payload).then((res) => res.data);
