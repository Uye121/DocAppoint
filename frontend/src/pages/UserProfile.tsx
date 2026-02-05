import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";

import { useAuth } from "../../hooks/useAuth";
import { assets } from "../assets/assets_frontend/assets";
import { getPatientInfo, updatePatientInfo } from "../api/patient";
import { Spinner } from "../components";
import type { PatientDetail } from "../types/patient";
import type { User } from "../types/user";
import { US_STATES } from "../../utils/states";

const UserProfile = (): React.JSX.Element => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isEdit, setIsEdit] = useState(false);
  const [localData, setLocalData] = useState<PatientDetail>({});

  const { data: patientData, isLoading } = useQuery({
    queryKey: ["patient-info", user?.id],
    queryFn: () => getPatientInfo(),
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<PatientDetail>) =>
      updatePatientInfo(user!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient-info"] });
      setIsEdit(false);
    },
  });

  useEffect(() => {
    if (patientData) {
      setLocalData(patientData);
    }
  }, [patientData]);

  const handleSave = () => {
    if (localData) {
      updateMutation.mutate(localData);
    }
  };

  const handleCancel = () => {
    if (patientData) {
      setLocalData(patientData);
    }
    setIsEdit(false);
  };

  const handleInputChange = (
    field: keyof PatientDetail,
    value: string | number,
  ) => {
    setLocalData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleUserFieldChange = (field: keyof User, value: string) => {
    setLocalData((prev) => ({
      ...prev,
      user: prev.user
        ? {
            ...prev.user,
            [field]: value,
          }
        : undefined,
    }));
  };

  if (isLoading) {
    return <Spinner loadingText="Loading profile information..." />;
  }

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "";
    try {
      const date = parseISO(dateString);
      return format(date, "MMMM d, yyyy");
    } catch {
      return dateString;
    }
  };

  const formatFullAddress = () => {
    const parts = [];

    if (localData.user?.addressLine1) parts.push(localData.user.addressLine1);
    if (localData.user?.addressLine2) parts.push(localData.user.addressLine2);

    const cityStateZip = [];
    if (localData.user?.city) cityStateZip.push(localData.user.city);
    if (localData.user?.state) {
      const stateName =
        US_STATES.find((s) => s.value === localData.user?.state)?.label ||
        localData.user.state;
      cityStateZip.push(stateName);
    }
    if (localData.user?.zipCode) cityStateZip.push(localData.user.zipCode);

    if (cityStateZip.length > 0) {
      parts.push(cityStateZip.join(", "));
    }

    if (parts.length === 0) return "Not provided";

    return parts.join("\n");
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-center gap-6">
          <img
            className="w-24 h-24 rounded-lg object-cover bg-primary-light"
            src={assets.profile_pic}
            alt="User Profile"
          />
          <div>
            {isEdit ? (
              <div className="flex flex-col gap-3">
                <div className="flex gap-3">
                  <input
                    className="px-3 py-2 border border-zinc-300 rounded-md text-2xl font-semibold text-neutral-800 w-32 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    type="text"
                    value={localData.user?.firstName || ""}
                    onChange={(e) =>
                      handleUserFieldChange("firstName", e.target.value)
                    }
                    placeholder="First name"
                  />
                  <input
                    className="px-3 py-2 border border-zinc-300 rounded-md text-2xl font-semibold text-neutral-800 w-32 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    type="text"
                    value={localData.user?.lastName || ""}
                    onChange={(e) =>
                      handleUserFieldChange("lastName", e.target.value)
                    }
                    placeholder="Last name"
                  />
                </div>
              </div>
            ) : (
              <h1 className="text-3xl font-semibold text-neutral-800">
                {localData.user?.firstName} {localData.user?.lastName}
              </h1>
            )}
            <p className="text-zinc-500 mt-1">{localData.user?.email}</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Contact Information */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-neutral-800 mb-4 pb-3 border-b">
            Contact Information
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Email
              </label>
              <p className="text-primary">{localData.user?.email}</p>
              {isEdit && (
                <p className="text-xs text-zinc-500 mt-1">
                  Email cannot be edited. Contact support to update your email
                  address.
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Phone Number
              </label>
              {isEdit ? (
                <input
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  type="tel"
                  value={localData.user?.phoneNumber || ""}
                  onChange={(e) =>
                    handleUserFieldChange("phoneNumber", e.target.value)
                  }
                  placeholder="(123) 456-7890"
                />
              ) : (
                <p
                  className={
                    localData.user?.phoneNumber
                      ? "text-primary"
                      : "text-zinc-400"
                  }
                >
                  {localData.user?.phoneNumber || "Not provided"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Address
              </label>
              {isEdit ? (
                <div className="space-y-3">
                  <div>
                    <input
                      className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      type="text"
                      value={localData.user?.addressLine1 || ""}
                      onChange={(e) =>
                        handleUserFieldChange("addressLine1", e.target.value)
                      }
                      placeholder="Street address"
                    />
                  </div>
                  <div>
                    <input
                      className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      type="text"
                      value={localData.user?.addressLine2 || ""}
                      onChange={(e) =>
                        handleUserFieldChange("addressLine2", e.target.value)
                      }
                      placeholder="Apt, suite, etc. (optional)"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <input
                        className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        type="text"
                        value={localData.user?.city || ""}
                        onChange={(e) =>
                          handleUserFieldChange("city", e.target.value)
                        }
                        placeholder="City"
                      />
                    </div>
                    <div>
                      <select
                        className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
                        value={localData.user?.state || ""}
                        onChange={(e) =>
                          handleUserFieldChange("state", e.target.value)
                        }
                      >
                        <option value="">Select a state</option>
                        {US_STATES.map((state) => (
                          <option key={state.value} value={state.value}>
                            {state.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <input
                        className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        type="text"
                        value={localData.user?.zipCode || ""}
                        onChange={(e) =>
                          handleUserFieldChange("zipCode", e.target.value)
                        }
                        placeholder="ZIP Code"
                        maxLength={10}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div
                  className={
                    localData.user?.addressLine1
                      ? "text-zinc-700 whitespace-pre-line"
                      : "text-zinc-400 whitespace-pre-line"
                  }
                >
                  {formatFullAddress()}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Basic Information */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-neutral-800 mb-4 pb-3 border-b">
            Basic Information
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Date of Birth
              </label>
              {isEdit ? (
                <input
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  type="date"
                  value={localData.user?.dateOfBirth || ""}
                  onChange={(e) =>
                    handleUserFieldChange("dateOfBirth", e.target.value)
                  }
                />
              ) : (
                <p
                  className={
                    localData.user?.dateOfBirth
                      ? "text-zinc-700"
                      : "text-zinc-400"
                  }
                >
                  {formatDate(localData.user?.dateOfBirth) || "Not provided"}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Medical Information */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-neutral-800 mb-4 pb-3 border-b">
            Medical Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Blood Type
              </label>
              {isEdit ? (
                <input
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  type="text"
                  value={localData.bloodType || ""}
                  onChange={(e) =>
                    handleInputChange("bloodType", e.target.value)
                  }
                  placeholder="e.g., O+"
                />
              ) : (
                <p
                  className={
                    localData.bloodType ? "text-zinc-700" : "text-zinc-400"
                  }
                >
                  {localData.bloodType || "Not provided"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Allergies
              </label>
              {isEdit ? (
                <textarea
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent min-h-[80px] resize-y"
                  value={localData.allergies || ""}
                  onChange={(e) =>
                    handleInputChange("allergies", e.target.value)
                  }
                  placeholder="List any allergies"
                />
              ) : (
                <p
                  className={
                    localData.allergies ? "text-zinc-700" : "text-zinc-400"
                  }
                >
                  {localData.allergies || "None reported"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Chronic Conditions
              </label>
              {isEdit ? (
                <textarea
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent min-h-[80px] resize-y"
                  value={localData.chronicConditions || ""}
                  onChange={(e) =>
                    handleInputChange("chronicConditions", e.target.value)
                  }
                  placeholder="List any chronic conditions"
                />
              ) : (
                <p
                  className={
                    localData.chronicConditions
                      ? "text-zinc-700"
                      : "text-zinc-400"
                  }
                >
                  {localData.chronicConditions || "None reported"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Current Medications
              </label>
              {isEdit ? (
                <textarea
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent min-h-[80px] resize-y"
                  value={localData.currentMedications || ""}
                  onChange={(e) =>
                    handleInputChange("currentMedications", e.target.value)
                  }
                  placeholder="List current medications"
                />
              ) : (
                <p
                  className={
                    localData.currentMedications
                      ? "text-zinc-700"
                      : "text-zinc-400"
                  }
                >
                  {localData.currentMedications || "None reported"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-600 mb-1">
                Insurance Provider
              </label>
              {isEdit ? (
                <input
                  className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  type="text"
                  value={localData.insurance || ""}
                  onChange={(e) =>
                    handleInputChange("insurance", e.target.value)
                  }
                  placeholder="e.g., Blue Shield"
                />
              ) : (
                <p
                  className={
                    localData.insurance ? "text-zinc-700" : "text-zinc-400"
                  }
                >
                  {localData.insurance || "Not provided"}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  Height (cm)
                </label>
                {isEdit ? (
                  <input
                    className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    type="number"
                    value={localData.height || ""}
                    onChange={(e) =>
                      handleInputChange("height", Number(e.target.value))
                    }
                    min="0"
                    step="0.1"
                  />
                ) : (
                  <p
                    className={
                      localData.height ? "text-zinc-700" : "text-zinc-400"
                    }
                  >
                    {localData.height
                      ? `${localData.height} cm`
                      : "Not provided"}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-600 mb-1">
                  Weight (kg)
                </label>
                {isEdit ? (
                  <input
                    className="w-full px-3 py-2 border border-zinc-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    type="number"
                    value={localData.weight || ""}
                    onChange={(e) =>
                      handleInputChange("weight", Number(e.target.value))
                    }
                    min="0"
                    step="0.1"
                  />
                ) : (
                  <p
                    className={
                      localData.weight ? "text-zinc-700" : "text-zinc-400"
                    }
                  >
                    {localData.weight
                      ? `${localData.weight} kg`
                      : "Not provided"}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex gap-4 justify-end">
        {isEdit ? (
          <>
            <button
              className="px-6 py-2.5 border border-zinc-300 text-zinc-700 font-medium rounded-lg hover:bg-zinc-50 transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-300 focus:ring-offset-2"
              onClick={handleCancel}
              disabled={updateMutation.isPending}
            >
              Cancel
            </button>
            <button
              className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </button>
          </>
        ) : (
          <button
            className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            onClick={() => setIsEdit(true)}
          >
            Edit Profile
          </button>
        )}
      </div>
    </div>
  );
};

export default UserProfile;
