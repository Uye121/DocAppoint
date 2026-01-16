import { useContext } from "react";

import { DoctorContext } from "../src/context";

export const useDoctor = () => {
  const ctx = useContext(DoctorContext);
  if (!ctx) throw new Error("useDoctor must be used inside DoctorProvider");
  return ctx;
};
