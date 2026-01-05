import React, { useEffect, useState } from "react";

import type { Speciality } from "../types/specialities";
import { getSpecialities as apiSpecialities } from "../api/specialities";
import { SpecialitiesContext } from "./SpecialitiesContext";

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
        const data = await getSpecialities();
        for (let i=0; i < data.length; i+= 1) {
          console.log(JSON.stringify(data[i]));
        }
        setSpecialities(data);
      } catch(err: unknown) {
        setError(err?.message ?? "Failed to load specialities");
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, []);

  const getSpecialities = async () => {
    const specs = await apiSpecialities();
    setSpecialities(specs);
    return specs
  };

  return (
    <SpecialitiesContext.Provider
      value={{ specialities, loading, error, getSpecialities }}
    >
      {children}
    </SpecialitiesContext.Provider>
  );
};
