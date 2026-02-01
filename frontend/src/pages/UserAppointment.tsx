import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { getPatientAppointments } from "../api/appointment";
import { Spinner, AppointmentCard } from "../components";

const UserAppointment = (): React.JSX.Element => {
  const nav = useNavigate();
  const { user, loading } = useAuth();
  const patientId = user?.id;

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ["patient-appointments", patientId],
    queryFn: () => getPatientAppointments(patientId!),
    enabled: !!patientId,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });

  if (isLoading || loading)
    return <Spinner loadingText="Loading appointments…" />;
  if (!user)
    return (
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex flex-col items-center justify-center min-h-100 text-center">
          <div className="w-16 h-16 mb-4 rounded-full bg-zinc-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-zinc-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-neutral-800 mb-2">
            Please log in to view appointments
          </h2>
          <p className="text-zinc-600 mb-6 max-w-md">
            Sign in to your account to see your upcoming and past appointments.
          </p>
          <button
            onClick={() => nav("/login")}
            className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            Go to Login
          </button>
        </div>
      </div>
    );

  const now = new Date();
  const upcoming = appointments.filter(
    (a) => new Date(a.appointmentStartDatetimeUtc) >= now,
  );
  const past = appointments.filter(
    (a) => new Date(a.appointmentStartDatetimeUtc) < now,
  );

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h2 className="pb-3 mt-6 font-semibold text-neutral-800 border-b">
        Upcoming
      </h2>
      {upcoming.length ? (
        <div className="grid gap-4 mt-4">
          {upcoming.map((a) => (
            <AppointmentCard
              item={a}
              isPast={false}
              key={a.id}
              userId={user!.id}
            />
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
            <AppointmentCard
              item={a}
              isPast={true}
              key={a.id}
              userId={user!.id}
            />
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 mt-4">No past appointments.</p>
      )}
    </div>
  );
};

export default UserAppointment;
