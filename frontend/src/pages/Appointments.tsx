import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  startOfWeek,
  endOfWeek,
  formatISO,
  addWeeks,
  eachDayOfInterval,
} from "date-fns";

import {
  DoctorCard,
  RelatedDoctors,
  Spinner,
  WeekSelector,
  SlotList,
} from "../components";
import { getDoctorById } from "../api/doctor";
import { getSlotsByRange, scheduleAppointment } from "../api/appointment";
import type { AppointmentPayload, Slot } from "../types/appointment";
import { useAuth } from "../../hooks/useAuth";

const Appointments = (): React.JSX.Element | null => {
  const minOffset = 0;
  const maxOffset = 2;
  const now = new Date();
  const [weekOffset, setWeekOffset] = useState<number>(0);
  const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const currentWeekStart = addWeeks(
    startOfWeek(now, { weekStartsOn: 1 }),
    weekOffset,
  );
  const currentWeekEnd = endOfWeek(currentWeekStart, { weekStartsOn: 1 });

  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { docId } = useParams<{ docId: string }>();
  const [selectedDay, setSelectedDay] = useState<string>(
    formatISO(now, { representation: "date" }),
  );
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [reason, setReason] = useState<string>("");
  const [booked, setBooked] = useState<boolean>(false);

  useEffect(() => {
    // Reset when selecting different days.
    setBooked(false);
    setReason("");
  }, [selectedDay, selectedSlot]);

  const { data: docInfo, isLoading } = useQuery({
    queryKey: ["doctor", docId],
    queryFn: () => getDoctorById(docId!),
    enabled: !!docId,
    staleTime: 5 * 60 * 1000, // 5 min cache
  });

  const goToCurrentWeek = () => {
    setWeekOffset(0);
    const todayStr = formatISO(now, { representation: "date" });
    setSelectedDay(todayStr);
    setSelectedSlot(null);
    setReason("");
  };

  const handleWeekChange = (delta: number) => {
    setWeekOffset((prev: number) => {
      const newOffset = prev + delta;
      const clamped = Math.min(maxOffset, Math.max(minOffset, newOffset));

      // Reset selected day to first day of current week when week changes
      if (clamped !== weekOffset) {
        const newWeekStart = addWeeks(
          startOfWeek(now, { weekStartsOn: 1 }),
          clamped,
        );
        const newWeekEnd = endOfWeek(newWeekStart, { weekStartsOn: 1 });
        const newDays = eachDayOfInterval({
          start: newWeekStart,
          end: newWeekEnd,
        });

        const todayStr = formatISO(now, { representation: "date" });
        const firstAvailableDay = newDays.find(
          (day) => formatISO(day, { representation: "date" }) >= todayStr,
        );

        if (firstAvailableDay) {
          setSelectedDay(
            formatISO(firstAvailableDay, { representation: "date" }),
          );
        }
      }

      return clamped;
    });
  };

  // Update the useQuery for slots
  const { data: docSlots = {} } = useQuery({
    queryKey: ["slots-range", docId, currentWeekStart],
    queryFn: () =>
      getSlotsByRange({
        providerId: docId!,
        startDate: currentWeekStart.toISOString().split("T")[0],
        endDate: currentWeekEnd.toISOString().split("T")[0],
      }),
    enabled: !!docId,
  });

  const slots = docSlots[selectedDay] || [];

  const handleBook = () => {
    if (!selectedSlot) return;

    const payload: AppointmentPayload = {
      provider: docId!,
      patient: user!.id,
      appointmentStartDatetimeUtc: selectedSlot.start,
      appointmentEndDatetimeUtc: selectedSlot.end,
      location: selectedSlot.hospitalId,
      reason: reason!,
    };

    scheduleAppointment(payload)
      .then(() => {
        queryClient.invalidateQueries({
          queryKey: ["slots-range", docId, currentWeekStart],
        });
        setBooked(true);
      })
      .catch((err) => alert(err));
  };

  if (isLoading) return <Spinner loadingText="Loading provider data..." />;
  if (!docInfo) return null;

  return (
    docInfo && (
      <div>
        <DoctorCard
          image={docInfo.user.image}
          firstName={docInfo.user.firstName}
          lastName={docInfo.user.lastName}
          education={docInfo.education}
          speciality={docInfo.specialityName}
          yearsOfExperience={docInfo.yearsOfExperience}
          about={docInfo.about}
          fees={docInfo.fees}
        />

        <div className="sm:ml-72 sm:pl-4 mt-4 font-medium text-gray-700">
          <WeekSelector
            selectedDay={selectedDay}
            onSelect={setSelectedDay}
            goToCurrentWeek={goToCurrentWeek}
            weekOffset={weekOffset}
            onWeekChange={handleWeekChange}
          />

          {/* SLOT LIST for selected day */}
          {selectedDay && (
            <div className="space-y-2">
              <SlotList
                slots={slots}
                userTz={userTimeZone}
                selectedId={selectedSlot?.id ?? null}
                onSelect={setSelectedSlot}
              />

              {selectedSlot?.id && (
                <div className="mt-3">
                  <label
                    htmlFor="reason"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Reason for visit <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="reason"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    rows={3}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Briefly describe the reason for your visit…"
                  />
                </div>
              )}

              {booked && (
                <div className="mt-3 p-3 rounded bg-green-50 text-green-800 text-sm">
                  &#9989; Appointment requested successfully! You will receive a
                  confirmation email once the provider confirms.
                </div>
              )}

              <div className="mt-4 text-center">
                <button
                  onClick={handleBook}
                  disabled={!selectedSlot?.id || !reason.trim()}
                  className={[
                    "px-6 py-2 rounded text-white",
                    selectedSlot?.id
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
