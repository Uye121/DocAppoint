import React, { useEffect, useState } from "react";

import type { Speciality } from "../types/speciality";
import { getSpecialities as apiGetSpecialities } from "../api/speciality";
import { SpecialityContext } from "./SpecialityContext";
import { getErrorMessage } from "../../utils/errorMap";

export const SpecialitiesProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [specialities, setSpecialities] = useState<Speciality[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const bootstrap = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await apiGetSpecialities();
        setSpecialities(data);
      } catch (err: unknown) {
        setError(getErrorMessage(err, "Failed to load specialities"));
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, []);

  const getSpecialities = async () => {
    const specs = await apiGetSpecialities();
    setSpecialities(specs);
    return specs;
  };

  return (
    <SpecialityContext.Provider
      value={{ specialities, loading, error, getSpecialities }}
    >
      {children}
    </SpecialityContext.Provider>
  );
};
