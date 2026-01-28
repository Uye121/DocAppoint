import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../../hooks/useAuth";
import { getPatientAppointments } from "../api/appointment";
import { Spinner, AppointmentCard } from "../components";

const UserAppointment = (): React.JSX.Element => {
  const { user } = useAuth();
  const patientId = user?.id;

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ["patient-appointments", patientId],
    queryFn: () => getPatientAppointments(patientId!),
    enabled: !!patientId,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });

  if (isLoading) return <Spinner loadingText="Loading appointments…" />;

  const now = new Date();
  const upcoming = appointments.filter(
    (a) => new Date(a.appointmentStartDatetimeUtc) >= now,
  );
  const past = appointments.filter(
    (a) => new Date(a.appointmentStartDatetimeUtc) < now,
  );

  /* ---------- render ---------- */
  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h2 className="pb-3 mt-6 font-semibold text-neutral-800 border-b">
        Upcoming
      </h2>
      {upcoming.length ? (
        <div className="grid gap-4 mt-4">
          {upcoming.map((a) => (
            <AppointmentCard item={a} isPast={false} key={a.id} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 mt-4">No upcoming appointments.</p>
      )}

      <h2 className="pb-3 mt-10 font-semibold text-neutral-800 border-b">
        Past
      </h2>
      {past.length ? (
        <div className="grid gap-4 mt-4">
          {past.map((a) => (
            <AppointmentCard item={a} isPast={true} key={a.id} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 mt-4">No past appointments.</p>
      )}
    </div>
  );
};

export default UserAppointment;
