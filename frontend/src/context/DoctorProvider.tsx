import React, { useEffect, useState } from "react";

import type { DoctorListItem } from "../types/doctor";
import { getDoctors as apiGetDoctors } from "../api/doctor";
import { DoctorContext } from "./DoctorContext";

export const DoctorProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [doctors, setDoctors] = useState<DoctorListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const bootstrap = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await apiGetDoctors();
        setDoctors(data);
      } catch (err: unknown) {
        setError(err?.message ?? "Failed to load doctors");
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, []);

  const getDoctors = async () => {
    const docs = await apiGetDoctors();
    setDoctors(docs);
    return docs;
  };

  return (
    <DoctorContext.Provider value={{ doctors, loading, error, getDoctors }}>
      {children}
    </DoctorContext.Provider>
  );
};
