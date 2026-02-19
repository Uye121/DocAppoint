import { describe, it, expect } from "vitest";
import { AxiosError } from "axios";

import { mock } from "../../../test/server";
import {
  getMedicalRecordByAppointment,
  createMedicalRecord,
  updateMedicalRecord,
} from "../medicalRecord";
import type {
  AppointmentDetails,
  DoctorDetails,
  HospitalDetails,
  MedicalRecordDetail,
  PatientDetails,
} from "../../types/medicalRecord";

const mockPatient: PatientDetails = {
  id: "1",
  bloodType: "A",
  allergies: "",
  chronicConditions: "",
  currentMedications: "",
  insurance: "",
  weight: 75,
  height: 170,
  fullName: "Mark Paul",
  dateOfBirth: "",
  image: "pic.jpg",
};

const mockProvider: DoctorDetails = {
  id: "2",
  specialityName: "pulmonologist",
  licenseNumber: "abc123",
  fullName: "John Doe",
};

const mockHospital: HospitalDetails = {
  id: 9,
  name: "General Hospital",
  phoneNumber: "123-456-7890",
  timezone: "US/NewYork",
};

const mockAppointment: AppointmentDetails = {
  startDatetimeUtc: "2026-01-21T22:30:00Z",
  endDatetimeUtc: "2026-01-21T23:00:00Z",
  reason: "test",
  status: "CONFIRMED",
};

const mockRecord: MedicalRecordDetail = {
  id: 1,
  patientDetails: mockPatient,
  providerDetails: mockProvider,
  hospitalDetails: mockHospital,
  appointmentDetails: mockAppointment,
  diagnosis: "respiratory infection",
  notes: "breathing problem",
  prescriptions: "ibuprofen",
  createdAt: "2026-01-21T21:30:00Z",
  updatedAt: "",
  createdBy: "2",
  updatedBy: "2",
  updatedByName: "John",
  createdByName: "John",
  isRemoved: false,
  removedAt: "",
};

describe("appointment API", () => {
  it("getMedicalRecordByAppointment GET /medical-record/", async () => {
    mock
      .onGet("/medical-record/", { params: { appointment: "1" } })
      .reply(200, [mockRecord]);
    const res = await getMedicalRecordByAppointment("1");
    expect(res).toEqual(mockRecord);
  });

  it("getMedicalRecordByAppointment GET /medical-record/ and returns null", async () => {
    mock
      .onGet("/medical-record/", { params: { appointment: "0" } })
      .reply(200, []);
    const res = await getMedicalRecordByAppointment("0");
    expect(res).toEqual(null);
  });

  it("createMedicalRecord POST /medical-record/", async () => {
    const payload = {
      patientId: mockPatient.id,
      hospitalId: mockHospital.id,
      appointmentId: "1",
      diagnosis: mockRecord.diagnosis,
      notes: mockRecord.notes,
      prescriptions: mockRecord.prescriptions,
    };
    mock.onPost("/medical-record/").reply(200, mockRecord);
    const res = await createMedicalRecord(payload);
    expect(res).toEqual(mockRecord);
  });

  it("createMedicalRecord POST /medical-record/ with 400 bad request error", async () => {
    const payload = {
      patientId: mockPatient.id,
      appointmentId: "1",
      diagnosis: mockRecord.diagnosis,
      notes: mockRecord.notes,
      prescriptions: mockRecord.prescriptions,
    };
    const res = {
      hospital_id: ["This field is required."],
    };
    mock.onPost("/medical-record/").reply(400, res);
    try {
      await createMedicalRecord(payload);
    } catch (error) {
      const axiosError = error as AxiosError;
      expect(axiosError.response?.status).toBe(400);
      expect(axiosError.response?.data).toEqual(res);
    }
  });

  it("updateMedicalRecord PATCH /medical-record/", async () => {
    const result = {
      patientId: mockPatient.id,
      hospitalId: mockHospital.id,
      appointmentId: "1",
      diagnosis: "strep throat",
      notes: mockRecord.notes,
      prescriptions: mockRecord.prescriptions,
    };
    const payload = {
      diagnosis: "strep throat",
    };
    mock.onPatch(`/medical-record/${mockRecord.id}/`).reply(200, result);
    const res = await updateMedicalRecord(mockRecord.id, payload);
    expect(res).toEqual(result);
  });
});
