import React, { useEffect, useState } from "react";
// import { doctors } from "../assets/assets_frontend/assets";
import type { AppContextValue } from "../types/app";
import { AppContext } from "./AppContext";
import { apiClient } from "../api/client";
import type { IDoctor } from "../types/app";

interface AppContextProviderProps {
  children: React.ReactNode;
}

const AppContextProvider: React.FC<AppContextProviderProps> = ({
  children,
}) => {
  const [doctors, setDoctors] = useState<IDoctor[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const currencySymbol = "$";

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        setLoading(true);
        let doctorData = await apiClient.get("/doctors");
        console.log(doctorData);

        doctorData = doctorData.map(
          (data: {
            id: number;
            firstName: string;
            lastName: string;
            image: string;
            speciality: { name: string };
            degree: string;
            experience: number;
            about: string;
            fees: string;
            addressLine1: string;
            addressLine2: string;
            city: string;
            state: string;
            zipCode: string;
          }) => ({
            id: data.id,
            name: `Dr. ${data.firstName} ${data.lastName}`,
            image: data.image,
            speciality: data.speciality.name,
            degree: data.degree,
            experience: `${Math.ceil(data.experience)} Years`,
            about: data.about,
            fees: data.fees,
            address: {
              line1: data.addressLine1,
              line2: data.addressLine2,
              city: data.city,
              state: data.state,
              zipCode: data.zipCode,
            },
          }),
        );

        setDoctors(doctorData);
        setError(null);
      } catch (err) {
        setError("Failed to retrieve doctors.");
        console.error("Error fetching doctor: ", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDoctors();
  }, []);

  const value: AppContextValue = {
    currencySymbol,
    doctors,
    loading,
    error,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContextProvider;
