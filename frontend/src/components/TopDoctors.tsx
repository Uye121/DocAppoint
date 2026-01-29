import React from "react";
import { useNavigate } from "react-router-dom";

import type { DoctorListItem } from "../types/doctor";
import { useDoctor } from "../../hooks/useDoctor";

const TopDoctors = (): React.JSX.Element => {
  const navigate = useNavigate();
  const { doctors } = useDoctor();

  return (
    <div className="flex flex-col items-center gap-4 my-16 text-foreground md:mx-10">
      <h2 className="text-3xl font-medium">Top Doctors to Book</h2>
      <p className="sm:w-1/3 text-center text-sm">
        Simply browse through our extensive list of trusted doctors.
      </p>
      <div className="w-full grid grid-cols-fluid gap-4 pt-5 gap-y-6 px-3 sm:px-0">
        {doctors?.slice(0, 10).map((item: DoctorListItem, index: number) => (
          <div
            onClick={() => {
              navigate(`/appointment/${item.id}`);
              scrollTo(0, 0);
            }}
            className="card-blue overflow-hidden cursor-pointer hover-lift"
            key={index}
          >
            <img
              className="bg-primary-light"
              src={item.image}
              alt={"Dr. " + item.lastName + "'s portrait"}
            />
            <div className="p-4">
              <div className="flex items-center gap-2 text-sm text-center text-success">
                <span className="w-2 h-2 bg-success rounded-full"></span>
                <p>Online</p>
              </div>
              <p className="text-foreground text-lg font-medium">
                {item.firstName + " " + item.lastName}
              </p>
              <p className="text-muted text-sm">{item.speciality}</p>
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={() => {
          navigate("/doctors");
          scrollTo(0, 0);
        }}
        className="btn-secondary text-gray-600 px-12 py-3 rounded-full mt-10"
      >
        more
      </button>
    </div>
  );
};

export default TopDoctors;
