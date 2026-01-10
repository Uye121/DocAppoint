import React, { useState } from "react";
import { useParams } from "react-router-dom";

import { useQuery } from "@tanstack/react-query";
import { SyncLoader } from "react-spinners";
import {
  eachDayOfInterval,
  format,
  startOfWeek,
  endOfWeek,
  formatISO,
} from "date-fns";
import { formatInTimeZone } from "date-fns-tz";

import { assets } from "../assets/assets_frontend/assets";
import { RelatedDoctors } from "../components";
import { getDoctorById } from "../api/doctor";
import { getSlotsByRange, scheduleAppointment } from "../api/appointment";
import type { AppointmentPayload, Slot } from "../types/appointment";
import { formatErrors } from "../../utils/errorMap";

const Appointments = (): React.JSX.Element | null => {
  const now = new Date();
  const monday = startOfWeek(new Date(), { weekStartsOn: 1 });
  const sunday = endOfWeek(new Date(), { weekStartsOn: 1 });
  const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const { docId } = useParams<{ docId: string }>();
  const [selectedDay, setSelectedDay] = useState<string>(
    formatISO(now, { representation: "date" }),
  );
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);
  const [selectedStartTime, setSelectedStartTime] = useState<string | null>(
    null,
  );
  const [selectedEndTime, setSelectedEndTime] = useState<string | null>(null);
  const [location, setLocation] = useState<string | null>(null);
  const [reason, setReason] = useState<string>("");
  const [booked, setBooked] = useState<bool>(false);

  const { data: docInfo, isLoading } = useQuery({
    queryKey: ["doctor", docId],
    queryFn: () => getDoctorById(docId!),
    enabled: !!docId,
    staleTime: 5 * 60 * 1000, // 5 min cache
  });

  const { data: docSlots = {} } = useQuery({
    queryKey: ["slots-range", docId, monday],
    queryFn: () =>
      getSlotsByRange({
        providerId: docId!,
        startDate: monday.toISOString().split("T")[0],
        endDate: sunday.toISOString().split("T")[0],
      }),
    enabled: !!docId,
  });

  const days = eachDayOfInterval({ start: monday, end: sunday });
  const slots = docSlots[selectedDay] || [];

  const handleBook = () => {
    if (!selectedSlotId) return;

    const payload: AppointmentPayload = {
      provider: docId!,
      appointmentStartDatetimeUtc: selectedStartTime!,
      appointmentEndDatetimeUtc: selectedEndTime!,
      location: location!,
      reason: reason!,
    };

    scheduleAppointment(payload)
      .then(() => setBooked(true))
      .catch((err) => alert(formatErrors(err)));
  };

  if (isLoading)
    return (
      <div className="flex flex-col items-center">
        <SyncLoader size={30} color="#38BDF8" loading />
        <p className="mt-4 text-zinc-600">Loading provider data...</p>
      </div>
    );

  return (
    docInfo && (
      <div>
        <div className="flex flex-col sm:flex-row gap-4">
          <div>
            <img
              className="bg-primary w-full sm:max-w-72 rounded-lg"
              src={docInfo.user.image}
              alt="Doctor's image"
            />
          </div>
          <div className="flex-1 border border-gray-400 rounded-lg p-8 py-7 bg-white mx-2 sm:mx-0 mt-[-80px] sm:mt-0">
            <p className="flex items-center gap-2 text-2xl font-medium text-gray-900">
              {docInfo.user.firstName + " " + docInfo.user.lastName}
              <img
                className="w-5"
                src={assets.verified_icon}
                alt="verification icon"
              />
            </p>
            <div className="flex items-center gap-2 text-sm mt-1 text-gray-600">
              <p>
                {docInfo.education} - {docInfo.specialityName}
              </p>
              <button className="py-0.5 px-2 border text-xs rounded-full">
                {docInfo.yearsOfExperience}
              </button>
            </div>
            <div>
              <p className="flex items-center gap-1 text-sm font-medium text-gray-900 mt-3">
                About <img src={assets.info_icon} alt="information icon" />
              </p>
              <p className="text-sm text-gray-500 max-w-[700px] mt-1">
                {docInfo.about}
              </p>
            </div>
            <p className="text-gray-500 font-medium mt-4">
              Appointment fee:{" "}
              <span className="text-gray-600">
                {"$"}
                {docInfo.fees}
              </span>
            </p>
          </div>
        </div>

        <div className="sm:ml-72 sm:pl-4 mt-4 font-medium text-gray-700">
          <div className="mb-4 border-b">
            <div className="flex gap-2">
              {days.map((day: Date) => {
                const dayKey = formatISO(day, { representation: "date" });
                const active = selectedDay === dayKey;
                const isPast = day < now;

                return (
                  <button
                    key={dayKey}
                    disabled={isPast}
                    onClick={() => setSelectedDay(dayKey)}
                    className={
                      "px-4 py-2 text-sm font-medium border-b-2 transition " +
                      (active
                        ? "border-primary text-primary"
                        : isPast
                          ? "border-transparent text-gray-300 cursor-not-allowed"
                          : "border-transparent text-gray-500 hover:text-gray-700")
                    }
                  >
                    {format(day, "EEE d")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* SLOT LIST for selected day */}
          {selectedDay && (
            <div className="space-y-2">
              {slots.length ? (
                slots.map((slot: Slot) => {
                  const isFree = slot.status === "FREE";
                  const hospitalTz =
                    slot.hospitalTimezone ?? "America/New_York";
                  console.log(slot);
                  const hospitalNow = formatInTimeZone(
                    new Date(),
                    hospitalTz,
                    "yyyy-MM-dd HH:mm:ss",
                  );
                  const hospitalSlotStart = formatInTimeZone(
                    slot.start,
                    hospitalTz,
                    "yyyy-MM-dd HH:mm:ss",
                  );
                  const isPast = hospitalSlotStart < hospitalNow;

                  const startLocal = formatInTimeZone(
                    slot.start,
                    userTimeZone,
                    "HH:mm",
                  );
                  const endLocal = formatInTimeZone(
                    slot.end,
                    userTimeZone,
                    "HH:mm",
                  );

                  return (
                    <button
                      key={slot.id}
                      onClick={() => {
                        if (isFree && !isPast) {
                          setSelectedSlotId(slot.id);
                          setSelectedStartTime(slot.start);
                          setSelectedEndTime(slot.end);
                          setLocation(slot.hospitalId);
                        }
                      }}
                      disabled={!isFree || isPast}
                      className={
                        "w-full rounded border px-4 py-3 text-left text-sm " +
                        (selectedSlotId === slot.id
                          ? "border-primary bg-primary/10"
                          : isFree && !isPast
                            ? "border-gray-200 hover:border-gray-400"
                            : "border-red-300 bg-red-50 text-red-700 cursor-not-allowed")
                      }
                    >
                      <div className="flex justify-between items-center">
                        <span>
                          {startLocal} – {endLocal}
                        </span>
                        <span className="text-xs text-gray-500">
                          {slot.hospitalName}
                        </span>
                      </div>
                    </button>
                  );
                })
              ) : (
                <p className="text-center text-gray-500">
                  No available slots this day.
                </p>
              )}

              {selectedSlotId && (
                <div className="mt-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason for visit <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    rows={3}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Briefly describe the reason for your visit…"
                  />
                </div>
              )}

              <div className="mt-4 text-center">
                <button
                  onClick={handleBook}
                  disabled={!selectedSlotId || !reason.trim()}
                  className={[
                    "px-6 py-2 rounded text-white",
                    selectedSlotId
                      ? "bg-primary hover:bg-primary-dark"
                      : "bg-gray-300 cursor-not-allowed",
                  ].join(" ")}
                >
                  Book Appointment
                </button>
              </div>
            </div>
          )}

          {!selectedDay && (
            <p className="text-center text-gray-500">
              Select a day to see available slots.
            </p>
          )}
        </div>

        <RelatedDoctors docId={docId} speciality={docInfo.specialityName} />
      </div>
    )
  );
};

export default Appointments;
