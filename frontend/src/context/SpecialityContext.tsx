import { createContext } from "react";
import type { SpecialityCtx } from "../types/speciality";

export const SpecialityContext = createContext<SpecialityCtx | undefined>(
  undefined,
);
