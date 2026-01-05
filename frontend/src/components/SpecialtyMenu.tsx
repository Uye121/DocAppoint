import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SyncLoader } from "react-spinners";

import type { Speciality } from "../types/specialities";
import { useSpecialities } from "../../hooks/useSpecialities";
import { formatErrors } from "../../utils/errorMap";

const SpecialtyMenu = (): React.JSX.Element => {
  const { specialities, loading, error, getSpecialities } = useSpecialities();
  const [specialityData, setSpecialityData] = useState([]);

  useEffect(() => {
    // apiClient
    //   .get("/specialities")
    //   .then((data) => setSpecialityData(data))
    //   .catch((error) => console.error("API Error: ", error));
    try {
      getSpecialities();
    } catch (err) {
      console.log(err);
      setError(formatErrors(err));
    }
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center">
        <SyncLoader size={30} color="#38BDF8" loading />
        <p className="mt-4 text-zinc-600">Retrieving data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16 text-red-600">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col items-center ggap-4 py-16 text-gray-800"
      id="specialty"
    >
      <h2 className="text-3xl font-medium">Find by Speciality</h2>
      <p className="sm:w-1/3 text-center text-sm">
        Simply browse through our extensive list of trusted doctors, schedule
        your appointment hassle-free.
      </p>
      <div className="flex sm:justify-center gap-4 pt-5 w-full overflow-scroll">
        {specialities && specialities.map((item: Speciality, index: number) => (
          <Link
            onClick={() => scrollTo(0, 0)}
            className="flex flex-col items-center text-xs cursor-pointer flex-shrink-0 hover:translate-y-[-10px] transition-all duration-500"
            key={index}
            to={`/doctors/${item.name}`}
          >
            <img className="w-16 sm:w-24 mb-2" src={item.image} alt="" />
            <p>{item.name}</p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default SpecialtyMenu;
