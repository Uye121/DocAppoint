import { useContext } from "react";

import { SpecialityContext } from "../src/context";

export const useSpeciality = () => {
  const ctx = useContext(SpecialityContext);
  if (!ctx)
    throw new Error("useSpecialties must be used inside SpecialitiesProvider");
  return ctx;
};
