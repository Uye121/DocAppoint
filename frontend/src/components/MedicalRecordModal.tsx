import React, { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { parse, format } from "date-fns";
import { useAuth } from "../../hooks/useAuth";
import {
  getMedicalRecordByAppointment,
  createMedicalRecord,
  updateMedicalRecord,
} from "../api/medicalRecord";
import type { AppointmentListItem } from "../types/appointment";
import type { MedicalRecordPayload } from "../types/medicalRecord";
import { Spinner } from "../components";
import { getErrorMessage } from "../../utils/errorMap";

interface MedicalRecordModalProps {
  selectedAppt: AppointmentListItem;
  show: boolean;
  onClose: () => void;
}

const MedicalRecordModal = ({
  selectedAppt,
  show,
  onClose,
}: MedicalRecordModalProps): React.JSX.Element | null => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [diagnosis, setDiagnosis] = useState("");
  const [notes, setNotes] = useState("");
  const [prescriptions, setPrescriptions] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  /* ---------- medical records ---------- */
  const { data: record, isLoading: recordLoading } = useQuery({
    queryKey: ["appointment-record", selectedAppt?.id],
    queryFn: () => getMedicalRecordByAppointment(selectedAppt!.id),
    enabled: !!selectedAppt?.id && show,
  });

  const medicalRecord = record;

  const resetForm = () => {
    setDiagnosis("");
    setNotes("");
    setPrescriptions("");
    setIsEditing(false);
  };

  useEffect(() => {
    if (medicalRecord) {
      setDiagnosis(medicalRecord.diagnosis);
      setNotes(medicalRecord.notes);
      setPrescriptions(medicalRecord.prescriptions);
    } else {
      resetForm();
    }
  }, [medicalRecord]);

  /* ---------- mutations ---------- */
  const createMutation = useMutation({
    mutationFn: (payload: MedicalRecordPayload) => createMedicalRecord(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["appointment-record", selectedAppt?.id],
      });
      setIsEditing(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: Partial<MedicalRecordPayload>;
    }) => updateMedicalRecord(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["appointment-record", selectedAppt?.id],
      });
      setIsEditing(false);
    },
  });

  const handleSaveRecord = async () => {
    if (!selectedAppt) return;

    const payload: MedicalRecordPayload = {
      patientId: selectedAppt.patientId,
      hospitalId: selectedAppt.hospital.id,
      appointmentId: selectedAppt.id,
      diagnosis,
      notes,
      prescriptions,
    };

    if (isEditing && medicalRecord) {
      updateMutation.mutate({
        id: medicalRecord.id,
        payload,
      });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleCloseModal = () => {
    resetForm();
    onClose();
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  if (!show) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
      onClick={handleCloseModal}
      data-testid="modal-backdrop"
    >
      <div
        className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold" data-testid="modal-title">
            Medical Record – {selectedAppt.patientName}
          </h2>
          <button
            onClick={handleCloseModal}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        {recordLoading ? (
          <div className="flex justify-center py-8">
            <Spinner loadingText="Loading record..." />
          </div>
        ) : (
          <>
            {/* Display View Mode */}
            {!isEditing && (
              <div className="space-y-6">
                {medicalRecord ? (
                  <>
                    {/* Appointment Information - Non-editable */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <h3 className="text-sm font-medium text-zinc-700 mb-3">
                        Appointment Details
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-zinc-500">Patient</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.fullName}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Provider</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.providerDetails?.fullName}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {medicalRecord.providerDetails?.specialityName} •{" "}
                            {medicalRecord.providerDetails?.licenseNumber}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Hospital</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.hospitalDetails?.name}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {medicalRecord.hospitalDetails?.phoneNumber} •{" "}
                            {medicalRecord.hospitalDetails?.timezone}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Appointment</p>
                          <p className="text-sm text-zinc-700">
                            Reason: {medicalRecord.appointmentDetails?.reason}
                          </p>
                          <p className="text-xs text-zinc-500">
                            Status: {medicalRecord.appointmentDetails?.status}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {medicalRecord.appointmentDetails
                              ?.startDatetimeUtc &&
                              format(
                                new Date(
                                  medicalRecord.appointmentDetails?.startDatetimeUtc,
                                ),
                                "PPp",
                              )}{" "}
                            -
                            {medicalRecord.appointmentDetails?.endDatetimeUtc &&
                              format(
                                new Date(
                                  medicalRecord.appointmentDetails?.endDatetimeUtc,
                                ),
                                "p",
                              )}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Patient Information */}
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <h3 className="text-sm font-medium text-zinc-700 mb-3">
                        Patient Information
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-zinc-500">Blood Type</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.bloodType ||
                              "Not provided"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Date of Birth</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.dateOfBirth
                              ? format(
                                  parse(
                                    medicalRecord.patientDetails?.dateOfBirth,
                                    "yyyy-MM-dd",
                                    new Date(),
                                  ),
                                  "PP",
                                )
                              : "Not provided"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Allergies</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.allergies ||
                              "None reported"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">
                            Chronic Conditions
                          </p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.chronicConditions ||
                              "None reported"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">
                            Current Medications
                          </p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.currentMedications ||
                              "None reported"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Insurance</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.insurance ||
                              "Not provided"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Weight</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.weight
                              ? `${medicalRecord.patientDetails.weight} kg`
                              : "Not provided"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Height</p>
                          <p className="text-sm text-zinc-700">
                            {medicalRecord.patientDetails?.height
                              ? `${medicalRecord.patientDetails.height} cm`
                              : "Not provided"}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Medical Record */}
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <h3 className="text-sm font-medium text-zinc-700 mb-3">
                        Medical Record
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <p className="text-xs text-zinc-500">Diagnosis</p>
                          <p className="text-sm text-zinc-700 whitespace-pre-wrap">
                            {medicalRecord.diagnosis}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Notes</p>
                          <p className="text-sm text-zinc-700 whitespace-pre-wrap">
                            {medicalRecord.notes}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Prescriptions</p>
                          <p className="text-sm text-zinc-700 whitespace-pre-wrap">
                            {medicalRecord.prescriptions}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Record Metadata */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <h3 className="text-sm font-medium text-zinc-700 mb-3">
                        Record Information
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-zinc-500">Created</p>
                          <p className="text-sm text-zinc-700">
                            {format(new Date(medicalRecord.createdAt), "PPp")}
                          </p>
                          <p className="text-xs text-zinc-500">
                            by {medicalRecord.createdByName}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500">Last Updated</p>
                          <p className="text-sm text-zinc-700">
                            {format(new Date(medicalRecord.updatedAt), "PPp")}
                          </p>
                          <p className="text-xs text-zinc-500">
                            by {medicalRecord.updatedByName}
                          </p>
                        </div>
                        {medicalRecord.isRemoved && (
                          <div className="md:col-span-2">
                            <p className="text-xs text-red-500">
                              Record has been removed
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Edit button */}
                    {medicalRecord.providerDetails?.id === user?.id && (
                      <div className="flex justify-end">
                        <button
                          onClick={() => setIsEditing(true)}
                          className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                        >
                          Edit Record
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-zinc-500 mb-4">
                      No medical record yet for this appointment.
                    </p>
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    >
                      Create Record
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Edit Mode */}
            {isEditing && (
              <div className="space-y-6">
                {medicalRecord && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <span className="font-medium">Last updated:</span>{" "}
                      {format(new Date(medicalRecord.updatedAt), "PPp")} by{" "}
                      {medicalRecord.updatedByName}
                    </p>
                  </div>
                )}

                {/* Medical Record - Editable */}
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h3 className="text-sm font-medium text-zinc-700 mb-3">
                    Medical Record
                  </h3>
                  <div>
                    <label
                      htmlFor="diagnosis"
                      className="block text-sm font-medium mb-1"
                    >
                      Diagnosis *
                    </label>
                    <textarea
                      id="diagnosis"
                      name="diagnosis"
                      value={diagnosis}
                      onChange={(e) => setDiagnosis(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 mb-4 focus:ring-2 focus:ring-primary focus:border-transparent"
                      rows={3}
                      required
                      disabled={isPending}
                    />

                    <label
                      htmlFor="notes"
                      className="block text-sm font-medium mb-1"
                    >
                      Notes *
                    </label>
                    <textarea
                      id="notes"
                      name="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 mb-4 focus:ring-2 focus:ring-primary focus:border-transparent"
                      rows={4}
                      required
                      disabled={isPending}
                    />

                    <label
                      htmlFor="prescriptions"
                      className="block text-sm font-medium mb-1"
                    >
                      Prescriptions *
                    </label>
                    <textarea
                      id="prescriptions"
                      name="prescriptions"
                      value={prescriptions}
                      onChange={(e) => setPrescriptions(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 mb-6 focus:ring-2 focus:ring-primary focus:border-transparent"
                      rows={3}
                      required
                      disabled={isPending}
                    />
                  </div>
                </div>

                <div className="flex gap-3 justify-end">
                  <button
                    onClick={() => {
                      if (medicalRecord) {
                        setDiagnosis(medicalRecord.diagnosis);
                        setNotes(medicalRecord.notes);
                        setPrescriptions(medicalRecord.prescriptions);
                        setIsEditing(false);
                      } else {
                        handleCloseModal();
                      }
                    }}
                    disabled={isPending}
                    className="px-6 py-2.5 border border-zinc-300 text-zinc-700 font-medium rounded-lg hover:bg-zinc-50 transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-300 focus:ring-offset-2"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveRecord}
                    disabled={
                      !(
                        diagnosis?.trim() &&
                        notes?.trim() &&
                        prescriptions?.trim()
                      ) || isPending
                    }
                    className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isPending
                      ? "Saving..."
                      : medicalRecord
                        ? "Update Record"
                        : "Create Record"}
                  </button>
                </div>

                {createMutation.isError && (
                  <p className="mt-4 text-sm text-red-600">
                    Error creating record:{" "}
                    {getErrorMessage(createMutation.error)}
                  </p>
                )}
                {updateMutation.isError && (
                  <p className="mt-4 text-sm text-red-600">
                    Error updating record:{" "}
                    {getErrorMessage(updateMutation.error)}
                  </p>
                )}

                {(createMutation.isSuccess || updateMutation.isSuccess) && (
                  <p className="mt-4 text-sm text-green-600">
                    Record successfully{" "}
                    {createMutation.isSuccess ? "created" : "updated"}!
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MedicalRecordModal;
