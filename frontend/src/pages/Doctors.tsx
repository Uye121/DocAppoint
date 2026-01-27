import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useDoctor } from "../../hooks/useDoctor";
import type { DoctorListItem } from "../types/doctor";

const Doctors = (): React.JSX.Element => {
  const navigate = useNavigate();
  const { speciality } = useParams();
  const [filteredDoc, setFilteredDoc] = useState<DoctorListItem[]>([]);
  const [showFilter, setShowFilter] = useState(false);
  const { doctors } = useDoctor();

  useEffect(() => {
    const applyFilter = () => {
      if (speciality) {
        setFilteredDoc(
          doctors!.filter(
            (doc: DoctorListItem) => doc.specialityName == speciality,
          ),
        );
      } else {
        setFilteredDoc(doctors || []);
      }
    };

    applyFilter();
  }, [speciality, doctors]);

  return (
    <div>
      <p className="text-gray-600">Browse through the doctors specialist.</p>
      <div className="flex flex-col sm:flex-row items-start gap-5 mt-5">
        <button
          className={`py-1 px-3 border rounded text-sm transition-all sm:hidden ${showFilter ? "bg-primary text-white" : ""}`}
          onClick={() => setShowFilter((prev) => !prev)}
        >
          Filters
        </button>
        <div
          className={`flex flex-col gap-4 text-sm text-gray-600 ${showFilter ? "flex" : "hidden sm:flex"}`}
        >
          <button
            type="button"
            onClick={() =>
              speciality == "General physician"
                ? navigate("/doctors")
                : navigate("/doctors/General physician")
            }
            className={`w-[94vw] sm:w-auto pl-3 py-1.5 pr-16 border border-gray-300 rounded transition-all text-left ${speciality === "General Physician" ? "bg-indigo-100 text-black" : "bg-white"}`}
          >
            General Physician
          </button>
          <button
            type="button"
            onClick={() =>
              speciality == "Gynecologist"
                ? navigate("/doctors")
                : navigate("/doctors/Gynecologist")
            }
            className={`w-[94vw] sm:w-auto pl-3 py-1.5 pr-16 border border-gray-300 rounded transition-all text-left ${speciality === "Gynecologist" ? "bg-indigo-100 text-black" : "bg-white"}`}
          >
            Gynecologist
          </button>
          <button
            type="button"
            onClick={() =>
              speciality == "Dermatologist"
                ? navigate("/doctors")
                : navigate("/doctors/Dermatologist")
            }
            className={`w-[94vw] sm:w-auto pl-3 py-1.5 pr-16 border border-gray-300 rounded transition-all text-left ${speciality === "Dermatologist" ? "bg-indigo-100 text-black" : "bg-white"}`}
          >
            Dermatologist
          </button>
          <button
            type="button"
            onClick={() =>
              speciality == "Pediatricians"
                ? navigate("/doctors")
                : navigate("/doctors/Pediatricians")
            }
            className={`w-[94vw] sm:w-auto pl-3 py-1.5 pr-16 border border-gray-300 rounded transition-all text-left ${speciality === "Pediatricians" ? "bg-indigo-100 text-black" : "bg-white"}`}
          >
            Pediatricians
          </button>
          <button
            type="button"
            onClick={() =>
              speciality == "Neurologist"
                ? navigate("/doctors")
                : navigate("/doctors/Neurologist")
            }
            className={`w-[94vw] sm:w-auto pl-3 py-1.5 pr-16 border border-gray-300 rounded transition-all text-left ${speciality === "Neurologist" ? "bg-indigo-100 text-black" : "bg-white"}`}
          >
            Neurologist
          </button>
        </div>
        <div className="w-full grid grid-cols-fluid gap-4 gap-y-6">
          {filteredDoc.map((item: DoctorListItem, index: number) => (
            <button
              type="button"
              onClick={() => navigate(`/appointment/${item.id}`)}
              className="border border-blue-200 rounded-xl overflow-hidden cursor-pointer hover:translate-y-[-10px] transition-all duration-500 text-left bg-white p-0"
              key={index}
            >
              <img
                className="bg-blue-50"
                src={item?.image}
                alt={"Dr. " + item?.lastName + "'s portrait"}
              />
              <div className="p-4">
                <div className="flex items-center gap-2 text-sm text-center text-green-500">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <p>Online</p>
                </div>
                <p className="text-gray-900 text-lg font-medium">
                  {item?.firstName + " " + item?.lastName}
                </p>
                <p className="text-gray-600 text-sm">{item.specialityName}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Doctors;
