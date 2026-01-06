import React, { useContext, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { SyncLoader } from "react-spinners";

import { assets } from "../assets/assets_frontend/assets";
import type { Doctor } from "../types/doctor";
import { RelatedDoctors } from "../components";
import { getDoctorById } from "../api/doctor";

const Appointments = (): React.JSX.Element | null => {
  const { docId } = useParams();
  // const { doctors, currencySymbol } = useContext(AppContext);
  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

  const [docInfo, setDocInfo] = useState<IDoctor | null>(null);
  const [docSlots, setDocSlots] = useState<TimeSlotType[][] | null>(null);
  const [slotIndex, setSlotIndex] = useState<number>(0);
  const [slotTime, setSlotTime] = useState<string>("");

  const { data, isLoading } = useQuery({
    queryKey: ["doctor", docId],
    queryFn: () => getDoctorById(docId!),
    enabled: !!docId,
    staleTime: 5 * 60 * 1000, // 5 min cache
  });

  console.log("appointment: ", data);

  // useEffect(() => {
  //   const getAvailableSlots = async () => {
  //     setDocSlots([]);

  //     const today = new Date();
  //     for (let i = 0; i < 7; i += 1) {
  //       const currentDate = new Date(today);
  //       currentDate.setDate(today.getDate() + i);

  //       const endTime = new Date();
  //       endTime.setDate(today.getDate() + i);
  //       endTime.setHours(21, 0, 0, 0);

  //       if (today.getDate() == currentDate.getDate()) {
  //         currentDate.setHours(
  //           currentDate.getHours() > 10 ? currentDate.getHours() + 1 : 10,
  //         );
  //         currentDate.setMinutes(currentDate.getMinutes() > 30 ? 30 : 0);
  //       } else {
  //         currentDate.setHours(10);
  //         currentDate.setMinutes(0);
  //       }

  //       const timeSlots: TimeSlotType[] = [];
  //       while (currentDate < endTime) {
  //         const formattedTime = currentDate.toLocaleTimeString([], {
  //           hour: "2-digit",
  //           minute: "2-digit",
  //         });

  //         timeSlots.push({
  //           datetime: new Date(currentDate),
  //           time: formattedTime,
  //         });

  //         currentDate.setMinutes(currentDate.getMinutes() + 30);
  //       }

  //       setDocSlots((prev) => {
  //         const previous = prev || [];
  //         return [...previous, timeSlots];
  //       });
  //     }
  //   };

  //   // getAvailableSlots();
  // }, [docInfo]);

  if (isLoading)
    return (
      <div className="flex flex-col items-center">
        <SyncLoader size={30} color="#38BDF8" loading />
        <p className="mt-4 text-zinc-600">Verifying your email...</p>
      </div>
    );

  return (
    data && (
      <div>
        <div className="flex flex-col sm:flex-row gap-4">
          <div>
            <img
              className="bg-primary w-full sm:max-w-72 rounded-lg"
              src={data.user.image}
              alt=""
            />
          </div>
          <div className="flex-1 border border-gray-400 rounded-lg p-8 py-7 bg-white mx-2 sm:mx-0 mt-[-80px] sm:mt-0">
            <p className="flex items-center gap-2 text-2xl font-medium text-gray-900">
              {data.user.firstName + " " + data.user.lastName}
              <img
                className="w-5"
                src={assets.verified_icon}
                alt="verification icon"
              />
            </p>
            <div className="flex items-center gap-2 text-sm mt-1 text-gray-600">
              <p>
                {data.education} - {data.specialityName}
              </p>
              <button className="py-0.5 px-2 border text-xs rounded-full">
                {data.yearsOfExperience}
              </button>
            </div>
            <div>
              <p className="flex items-center gap-1 text-sm font-medium text-gray-900 mt-3">
                About <img src={assets.info_icon} alt="information icon" />
              </p>
              <p className="text-sm text-gray-500 max-w-[700px] mt-1">
                {data.about}
              </p>
            </div>
            <p className="text-gray-500 font-medium mt-4">
              Appointment fee:{" "}
              <span className="text-gray-600">
                {"$"}
                {data.fees}
              </span>
            </p>
          </div>
        </div>

        <div className="sm:ml-72 sm:pl-4 mt-4 font-medium text-gray-700">
          <p>Booking Slots</p>
          <div className="flex gap-3 items-center w-full overflow-x-scroll mt-4">
            {docSlots?.length &&
              docSlots?.map((slot, index) => (
                <div
                  onClick={() => setSlotIndex(index)}
                  className={`text-center py-6 min-w-16 rounded-full cursor-pointer ${slotIndex == index ? "bg-primary" : "border border-gray-200"}`}
                  key={index}
                >
                  <p>{slot[0] && daysOfWeek[slot[0].datetime.getDay()]}</p>
                  <p>{slot[0] && slot[0].datetime.getDate()}</p>
                </div>
              ))}
          </div>
          <div className="flex items-center gap-3 w-full overflow-x-scroll mt-4">
            {docSlots?.length &&
              docSlots[slotIndex].map((item, index) => (
                <p
                  onClick={() => setSlotTime(item.time)}
                  className={`text-sm font-light flex-shrink-0 px-5 py-2 rounded-full cursor-pointer ${item.time == slotTime ? "bg-primary text-white" : "text-gray-400 border border-gray-300"}`}
                  key={index}
                >
                  {item.time.toLowerCase()}
                </p>
              ))}
          </div>
          <button className="bg-primary text-white text-sm font-light px-14 py-3 rounded-full my-6">
            Book an Appointment
          </button>
        </div>

        <RelatedDoctors docId={docId} speciality={data.speciality} />
      </div>
    )
  );
};

export default Appointments;
