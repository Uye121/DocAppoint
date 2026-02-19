import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { useAuth } from "../../hooks/useAuth";
import {
  getProviderAppointments,
  updateAppointmentStatus,
} from "../api/appointment";
import type { AppointmentListItem } from "../types/appointment";
import { Spinner, MedicalRecordModal } from "../components";
import { getErrorMessage } from "../../utils/errorMap";

const ProviderHome = (): React.JSX.Element => {
  const { user } = useAuth();
  const providerId = user?.id;

  const [selectedAppt, setSelectedAppt] = useState<AppointmentListItem | null>(
    null,
  );
  const [showRecords, setShowRecords] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ---------- appointments ---------- */
  const {
    data: appointments = [],
    isLoading,
    refetch: refetchAppts,
  } = useQuery({
    queryKey: ["provider-appointments", providerId],
    queryFn: () => getProviderAppointments(providerId!),
    enabled: !!providerId,
    staleTime: 3,
    refetchOnWindowFocus: true,
  });

  const handleStatus = async (appt: AppointmentListItem, status: string) => {
    try {
      await updateAppointmentStatus(appt.id, status);
      refetchAppts();
    } catch (err) {
      const errMsg = getErrorMessage(err);
      setError(errMsg);
      console.error("Failed to update appointment status:", errMsg);
    }
  };

  const handleCloseModal = () => {
    setShowRecords(false);
    setSelectedAppt(null);
  };

  if (isLoading) return <Spinner loadingText="Loading appointments..." />;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6 grid md:grid-cols-3 gap-6">
        {/* Left column – appointment tabs */}
        <div className="md:col-span-2 space-y-6">
          {/* Error message display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          {["REQUESTED", "CONFIRMED", "RESCHEDULED"].map((st) => (
            <section
              key={st}
              className="bg-white rounded-xl border border-gray-200 p-4"
            >
              <h3 className="font-semibold text-gray-800 mb-3">
                {st} Appointments
              </h3>
              <div className="space-y-3">
                {appointments
                  .filter((a) => a.status === st)
                  .map((appt) => (
                    <div
                      key={appt.id}
                      className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-primary transition gap-3"
                    >
                      {/* Left side - patient info */}
                      <div className="flex-1 min-w-0 w-full sm:w-auto">
                        <p className="font-medium text-gray-900 truncate">
                          {appt.patientName}
                        </p>
                        <div className="flex flex-col xs:flex-row xs:items-center gap-1 xs:gap-2">
                          <p className="text-xs sm:text-sm text-gray-600 truncate">
                            {format(
                              new Date(appt.appointmentStartDatetimeUtc),
                              "PPp",
                            )}
                          </p>
                          <p className="text-xs text-gray-500 truncate xs:border-l xs:border-gray-300 xs:pl-2">
                            {appt.reason}
                          </p>
                        </div>
                      </div>

                      {/* Right side */}
                      <div className="flex flex-wrap items-center justify-start sm:justify-end gap-2 w-full sm:w-auto">
                        {st === "REQUESTED" && (
                          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
                            <button
                              onClick={() => handleStatus(appt, "CONFIRMED")}
                              className="flex-1 sm:flex-auto px-3 py-1.5 rounded bg-emerald-400 text-white text-xs hover:bg-green-600 whitespace-nowrap"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => handleStatus(appt, "CANCELLED")}
                              className="flex-1 sm:flex-auto px-3 py-1.5 rounded bg-red-500 text-white text-xs hover:bg-red-600 whitespace-nowrap"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                        {st === "CONFIRMED" && (
                          <button
                            onClick={() => {
                              setSelectedAppt(appt);
                              setShowRecords(true);
                            }}
                            className="flex-1 sm:flex-auto px-3 py-1.5 rounded bg-primary text-white text-xs hover:bg-primary-dark whitespace-nowrap"
                          >
                            Add/View Record
                          </button>
                        )}
                        <span className="px-2 py-1 rounded text-xs bg-yellow-200 text-yellow-800 whitespace-nowrap">
                          {st}
                        </span>
                      </div>
                    </div>
                  ))}
                {appointments.filter((a) => a.status === st).length === 0 && (
                  <p className="text-sm text-gray-500">
                    No {st.toLowerCase()} appointments.
                  </p>
                )}
              </div>
            </section>
          ))}
        </div>

        {/* Right column */}
        <aside className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-800 mb-3">Today</h3>
            <p className="text-sm text-gray-600">
              {
                appointments.filter((a) => {
                  const d = new Date(a.appointmentStartDatetimeUtc);
                  return (
                    d.toDateString() === new Date().toDateString() &&
                    a.status === "CONFIRMED"
                  );
                }).length
              }{" "}
              appointments
            </p>
          </div>
        </aside>
      </main>

      {/* Medical Record modal */}
      {selectedAppt && (
        <MedicalRecordModal
          selectedAppt={selectedAppt}
          show={showRecords}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default ProviderHome;
