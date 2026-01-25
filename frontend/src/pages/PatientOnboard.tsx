import { useState } from "react";
import { useNavigate } from "react-router-dom";

import type { Patient } from "../types/patient";
import { onboard } from "../api/patient";
import { useAuth } from "../../hooks/useAuth";

const PatientOnboard = () => {
  const nav = useNavigate();
  const { refreshUser } = useAuth();
  const [form, setForm] = useState<Patient>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onboard(form);
      await refreshUser();
      nav("/");
    } catch (err) {
      console.log(err);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setForm((f) => ({
      ...f,
      [name]:
        name === "weight" || name === "height"
          ? Number(value) || undefined
          : value || undefined,
    }));
  };

  return (
    <form
      className="max-w-2xl mx-auto bg-white rounded-lg border border-gray-300 p-6 shadow-sm"
      onSubmit={handleSubmit}
    >
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Complete your profile
      </h2>
      <p className="text-sm text-gray-600 mb-6">
        All fields are optional and can be filled later.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="bloodType"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Blood type
          </label>
          <input
            id="bloodType"
            name="bloodType"
            value={form.bloodType ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g. O+"
          />
        </div>

        <div>
          <label
            htmlFor="insurance"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Insurance
          </label>
          <input
            id="insurance"
            name="insurance"
            value={form.insurance ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Provider / policy number"
          />
        </div>

        <div>
          <label
            htmlFor="weight"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Weight (kg)
          </label>
          <input
            id="weight"
            name="weight"
            type="number"
            value={form.weight ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="70"
          />
        </div>

        <div>
          <label
            htmlFor="height"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Height (cm)
          </label>
          <input
            id="height"
            name="height"
            type="number"
            value={form.height ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="175"
          />
        </div>
      </div>

      <div className="mt-4">
        <label
          htmlFor="allergies"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Allergies
        </label>
        <textarea
          id="allergies"
          name="allergies"
          value={form.allergies ?? ""}
          onChange={handleChange}
          rows={3}
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="List any known allergies"
        />
      </div>

      <div className="mt-4">
        <label
          htmlFor="chronicConditions"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Chronic conditions
        </label>
        <textarea
          id="chronicConditions"
          name="chronicConditions"
          value={form.chronicConditions ?? ""}
          onChange={handleChange}
          rows={3}
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="e.g. Diabetes, Hypertension"
        />
      </div>

      <div className="mt-4">
        <label
          htmlFor="currentMedications"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Current medications
        </label>
        <textarea
          id="currentMedications"
          name="currentMedications"
          value={form.currentMedications ?? ""}
          onChange={handleChange}
          rows={3}
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="List any medicines you are taking"
        />
      </div>

      <div className="mt-6 flex">
        <button
          onClick={handleSubmit}
          className="w-full mt-6 h-11 rounded-md bg-primary text-white font-medium
             disabled:opacity-60 disabled:cursor-not-allowed
             hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary"
        >
          Save profile
        </button>
      </div>
    </form>
  );
};

export default PatientOnboard;
