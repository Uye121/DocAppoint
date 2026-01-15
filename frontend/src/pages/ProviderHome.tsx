import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { useAuth } from "../../hooks/useAuth";
import { getProviderAppointments, updateAppointmentStatus } from "../api/appointment";
// import { getPatientMedicalRecords, createMedicalRecord, updateMedicalRecord } from "../api/medicalRecord";
import type { AppointmentListItem } from "../types";
import { Spinner } from "../components";

const ProviderHome = (): React.JSX.Element => {
  const { user } = useAuth();
  const providerId = user?.id;
  const [selectedAppt, setSelectedAppt] = useState<AppointmentListItem | null>(null);
  const [showRecords, setShowRecords] = useState(false);
  const [diagnosis, setDiagnosis] = useState("");
  const [notes, setNotes] = useState("");
  const [prescriptions, setPrescriptions] = useState("");
  const [editingRecord, setEditingRecord] = useState<number | null>(null);

  /* ---------- appointments ---------- */
  const { data: appointments = [], isLoading, refetch: refetchAppts } = useQuery({
    queryKey: ["provider-appointments", providerId],
    queryFn: () => getProviderAppointments(providerId!),
    enabled: !!providerId,
  });

  /* ---------- medical records ---------- */
  // const { data: records = [], refetch: refetchRecords } = useQuery({
  //   queryKey: ["records", selectedAppt?.patient.id],
  //   queryFn: () => getPatientMedicalRecords(selectedAppt!.patient.id),
  //   enabled: !!selectedAppt?.patient.id,
  // });
  const records = [];

  const handleStatus = async (appt: AppointmentListItem, status: string) => {
    await updateAppointmentStatus(appt.id, status);
    refetchAppts();
  };

  // const handleSaveRecord = async () => {
  //   const payload: MedicalRecordPayload = { diagnosis, notes, prescriptions };
  //   if (editingRecord) {
  //     await updateMedicalRecord(editingRecord, payload);
  //   } else {
  //     await createMedicalRecord({
  //       ...payload,
  //       patient: selectedAppt!.patient.id,
  //       healthcareProvider: providerId!,
  //     });
  //   }
  //   setDiagnosis(""); setNotes(""); setPrescriptions("");
  //   setEditingRecord(null);
  //   refetchRecords();
  // };

  if (isLoading) return <Spinner loadingText="Loading appointments..." />;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6 grid md:grid-cols-3 gap-6">
        {/* Left column – appointment tabs */}
        <div className="md:col-span-2 space-y-6">
          {["REQUESTED", "CONFIRMED", "RESCHEDULED"].map((st) => (
            <section key={st} className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-800 mb-3">{st} Appointments</h3>
              <div className="space-y-3">
                {appointments
                  .filter((a) => a.status === st)
                  .map((appt) => (
                    <div
                      key={appt.id}
                      className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-primary transition"
                    >
                      <div>
                        <p className="font-medium text-gray-900">
                          {appt.patient.user.firstName} {appt.patient.user.lastName}
                        </p>
                        <p className="text-sm text-gray-600">
                          {format(new Date(appt.appointmentStartDatetimeUtc), "PPp")}
                        </p>
                        <p className="text-xs text-gray-500">{appt.reason}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {st === "REQUESTED" && (
                          <>
                            <button
                              onClick={() => handleStatus(appt, "CONFIRMED")}
                              className="px-3 py-1.5 rounded bg-emerald-400 text-white text-xs hover:bg-green-600"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => handleStatus(appt, "CANCELLED")}
                              className="px-3 py-1.5 rounded bg-red-500 text-white text-xs hover:bg-red-600"
                            >
                              Reject
                            </button>
                          </>
                        )}
                        {st === "CONFIRMED" && (
                          <button
                            onClick={() => {
                              setSelectedAppt(appt);
                              setShowRecords(true);
                            }}
                            className="px-3 py-1.5 rounded bg-primary text-white text-xs hover:bg-primary-dark"
                          >
                            View Record
                          </button>
                        )}
                        <span className={"px-2 py-1 rounded text-xs bg-yellow-200 text-yellow-800"}>{st}</span>
                      </div>
                    </div>
                  ))}
                {appointments.filter((a) => a.status === st).length === 0 && (
                  <p className="text-sm text-gray-500">No {st.toLowerCase()} appointments.</p>
                )}
              </div>
            </section>
          ))}
        </div>

        {/* Right column – quick stats / upcoming */}
        <aside className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-800 mb-3">Today</h3>
            <p className="text-sm text-gray-600">
              {appointments.filter((a) => {
                const d = new Date(a.appointmentStartDatetimeUtc);
                return d.toDateString() === new Date().toDateString();
              }).length}{" "}
              appointments
            </p>
          </div>
        </aside>
      </main>

      {/* Medical Record modal */}
      {showRecords && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">
                Medical Records – {selectedAppt.patient.firstName} {selectedAppt.patient.lastName}
              </h2>
              <button onClick={() => setShowRecords(false)} className="text-gray-500">✕</button>
            </div>

            {/* History */}
            <div className="mb-4">
              <h3 className="font-medium mb-2">History</h3>
              {records.length === 0 && <p className="text-sm text-gray-500">No records yet.</p>}
              {records.map((r) => (
                <div key={r.id} className="border rounded p-3 mb-2">
                  <p className="text-sm font-medium">Diagnosis: {r.diagnosis}</p>
                  <p className="text-sm">Notes: {r.notes}</p>
                  <p className="text-sm">Prescriptions: {r.prescriptions}</p>
                  {r.healthcareProvider.id === user?.id && (
                    <button
                      onClick={() => {
                        setEditingRecord(r.id);
                        setDiagnosis(r.diagnosis);
                        setNotes(r.notes);
                        setPrescriptions(r.prescriptions);
                      }}
                      className="mt-2 text-xs text-blue-600 underline"
                    >
                      Edit
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Add / Edit form */}
            <div>
              <h3 className="font-medium mb-2">{editingRecord ? "Edit" : "Add"} Record</h3>
              <label className="block text-sm mb-1">Diagnosis *</label>
              <textarea
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                className="w-full border rounded px-3 py-2 mb-2"
                rows={2}
              />
              <label className="block text-sm mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full border rounded px-3 py-2 mb-2"
                rows={3}
              />
              <label className="block text-sm mb-1">Prescriptions</label>
              <textarea
                value={prescriptions}
                onChange={(e) => setPrescriptions(e.target.value)}
                className="w-full border rounded px-3 py-2 mb-3"
                rows={2}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSaveRecord}
                  disabled={!diagnosis.trim()}
                  className="px-4 py-2 rounded bg-primary text-white disabled:opacity-50"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setEditingRecord(null);
                    setDiagnosis("");
                    setNotes("");
                    setPrescriptions("");
                  }}
                  className="px-4 py-2 rounded border"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProviderHome;
