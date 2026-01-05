import { useContext } from "react";

import { SpecialitiesContext } from "../src/context";

export const useSpecialities = () => {
  const ctx = useContext(SpecialitiesContext);
  if (!ctx) throw new Error('useSpecialties must be used inside SpecialitiesProvider');
  return ctx; 
};
