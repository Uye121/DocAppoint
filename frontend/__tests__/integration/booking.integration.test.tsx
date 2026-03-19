import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  AuthProvider,
  SpecialitiesProvider,
  DoctorProvider,
} from "../../src/context";
import { Doctors, Appointments } from "../../src/pages";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Appointment Booking Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    vi.clearAllMocks();
    localStorage.clear();

    process.env.TZ = "UTC";
    vi.setSystemTime(new Date("2024-01-16T12:00:00Z"));
  });

  const renderDoctorsPage = (initialPath = "/doctors") => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Mock authenticated user
    mock.onGet("http://localhost:8000/api/users/me").reply(200, {
      id: "patient-123",
      email: "patient@example.com",
      firstName: "Test",
      lastName: "Patient",
      userRole: "patient",
      userName: "testpatient",
      hasPatientProfile: true,
      hasProviderProfile: false,
      hasAdminStaffProfile: false,
      hasSystemAdminProfile: false,
    });

    // Mock doctors data
    mock.onGet("http://localhost:8000/api/provider/").reply(200, [
      {
        id: 1,
        firstName: "John",
        lastName: "Smith",
        specialityName: "Cardiology",
        image: "doctor1.jpg",
      },
      {
        id: 2,
        firstName: "Sarah",
        lastName: "Johnson",
        specialityName: "Dermatology",
        image: "doctor2.jpg",
      },
      {
        id: 3,
        firstName: "Michael",
        lastName: "Chen",
        specialityName: "Neurology",
        image: "doctor3.jpg",
      },
      {
        id: 4,
        firstName: "Peter",
        lastName: "Doan",
        specialityName: "Cardiology",
        image: "doctor4.jpg",
      },
    ]);

    // Mock specialities data
    mock.onGet("http://localhost:8000/api/speciality/").reply(200, [
      { id: 1, name: "Cardiology", image: "cardio.jpg" },
      { id: 2, name: "Dermatology", image: "derma.jpg" },
      { id: 3, name: "Neurology", image: "neuro.jpg" },
    ]);

    // Set tokens
    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <Routes>
              <Route element={<ProtectedRoutes />}>
                <Route
                  element={
                    <SpecialitiesProvider>
                      <DoctorProvider>
                        <Outlet />
                      </DoctorProvider>
                    </SpecialitiesProvider>
                  }
                >
                  <Route path="/doctors" element={<Doctors />} />
                  <Route path="/doctors/:speciality" element={<Doctors />} />
                  <Route
                    path="/appointment/:docId"
                    element={<Appointments />}
                  />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it("should browse doctors list", async () => {
    renderDoctorsPage("/doctors");

    // Wait for doctors to load
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
    });

    expect(screen.getByText("Sarah Johnson")).toBeInTheDocument();
    expect(screen.getByText("Michael Chen")).toBeInTheDocument();

    // Verify specialities filter is visible
    expect(
      screen.getByRole("button", { name: "Cardiology" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Dermatology" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Neurology" }),
    ).toBeInTheDocument();
  });

  it("should filter doctors by speciality", async () => {
    renderDoctorsPage("/doctors");

    await waitFor(() => {
      // Check that ProtectedRoutes has user
      expect(
        screen.queryByRole("heading", { name: /login/i }),
      ).not.toBeInTheDocument();
    });

    // Wait for doctors to load
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
    });

    // Click the Filters button to show the filter panel on mobile
    const filtersButton = screen.getByText("Filters");
    await user.click(filtersButton);

    // Now the filter buttons should be visible
    const filterPanel = screen.getByTestId("filter-panel");
    const filterButtons = within(filterPanel).getAllByRole("button");
    filterButtons.forEach((btn, i) => {
      console.log(`Button ${i}:`, {
        text: btn.textContent,
        visible: btn.offsetParent !== null,
      });
    });

    // Find and click the Cardiology button
    const cardiologyButton = within(filterPanel).getByRole("button", {
      name: "Cardiology",
    });
    await user.click(cardiologyButton);

    // Should only show cardiologists
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
      expect(screen.queryByText("Sarah Johnson")).not.toBeInTheDocument();
      expect(screen.queryByText("Michael Chen")).not.toBeInTheDocument();
    });
  });

  it("should navigate to doctor appointment page", async () => {
    mock.onGet("http://localhost:8000/api/provider/1").reply(200, {
      id: "1",
      user: {
        id: "doc-123",
        firstName: "John",
        lastName: "Smith",
        email: "john.smith@example.com",
        image: "doctor1.jpg",
      },
      specialityName: "Cardiology",
      education: "Harvard Medical School",
      yearsOfExperience: 10,
      about: "Experienced cardiologist specializing in heart health.",
      fees: "150",
      licenseNumber: "LIC12345",
      hospitals: [1],
    });

    // Mock slots data
    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);

    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);

    mock
      .onGet("/api/slot/range/", {
        params: {
          provider: "1",
          start_date: today.toISOString().split("T")[0],
          end_date: sunday.toISOString().split("T")[0],
        },
      })
      .reply(200, {
        [todayStr]: [
          {
            id: "slot-1",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: `${todayStr}T09:00:00Z`,
            end: `${todayStr}T09:30:00Z`,
            status: "FREE",
          },
        ],
      });

    renderDoctorsPage("/doctors");

    // Wait for doctors to load
    await waitFor(() => {
      expect(screen.getByText("John Smith")).toBeInTheDocument();
    });

    // Click on a doctor
    await user.click(screen.getByText("John Smith"));

    // Should navigate to appointment page
    await waitFor(() => {
      expect(screen.getByText(/appointment fee/i)).toBeInTheDocument();
      expect(screen.getByText(/\$150/)).toBeInTheDocument();
      expect(screen.getByText(/harvard medical school/i)).toBeInTheDocument();
    });
  });

  it("should display available slots for selected date", async () => {
    mock.onGet("http://localhost:8000/api/provider/1").reply(200, {
      id: "1",
      user: {
        id: "doc-123",
        firstName: "John",
        lastName: "Smith",
        email: "john.smith@example.com",
        image: "doctor1.jpg",
      },
      specialityName: "Cardiology",
      education: "Harvard Medical School",
      yearsOfExperience: 10,
      about: "Experienced cardiologist specializing in heart health.",
      fees: "150",
      licenseNumber: "LIC12345",
      hospitals: [1],
    });

    const today = new Date("2024-01-16T12:00:00Z");
    const todayStr = today.toISOString().split("T")[0];

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split("T")[0];

    // Calculate Monday and Sunday for the week
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1); // Monday of current week
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6); // Sunday of current week

    const startDate = monday.toISOString().split("T")[0];
    const endDate = sunday.toISOString().split("T")[0];

    console.log("Mock params:", {
      provider: "1",
      start_date: startDate,
      end_date: endDate,
    });

    // Mock slots endpoint with params object
    mock
      .onGet("http://localhost:8000/api/slot/range/", {
        params: {
          provider: "1",
          start_date: startDate,
          end_date: endDate,
        },
      })
      .reply(200, {
        [todayStr]: [
          {
            id: "slot-1",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: `${todayStr}T09:00:00Z`,
            end: `${todayStr}T09:30:00Z`,
            status: "FREE",
          },
          {
            id: "slot-2",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: `${todayStr}T10:00:00Z`,
            end: `${todayStr}T10:30:00Z`,
            status: "FREE",
          },
          {
            id: "slot-3",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: `${todayStr}T11:00:00Z`,
            end: `${todayStr}T11:30:00Z`,
            status: "BOOKED",
          },
        ],
        [tomorrowStr]: [
          {
            id: "slot-4",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: `${tomorrowStr}T09:00:00Z`,
            end: `${tomorrowStr}T09:30:00Z`,
            status: "FREE",
          },
        ],
      });

    renderDoctorsPage("/appointment/1");

    await waitFor(
      () => {
        expect(screen.getByText(/John Smith/i)).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    expect(screen.getByText(/\$150/)).toBeInTheDocument();

    // Find and click tomorrow's date
    const tomorrowDay = tomorrow.getDate().toString();
    const dateButton = await screen.findByRole("button", {
      name: new RegExp(`^\\S+\\s+${tomorrowDay}$`),
    });
    await user.click(dateButton);

    // Wait for tomorrow's slot to load
    await waitFor(
      () => {
        expect(screen.getByText(/09:00 – 09:30/i)).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    // Verify tomorrow's slot is clickable
    const freeSlotButton = screen.getByText(/09:00 – 09:30/i).closest("button");
    expect(freeSlotButton).not.toBeDisabled();

    // Verify there's no 11:00 slot for tomorrow
    expect(screen.queryByText(/11:00 – 11:30/i)).not.toBeInTheDocument();
  });

  it("should select a slot and show reason input", async () => {
    mock.onGet("http://localhost:8000/api/provider/1").reply(200, {
      id: "1",
      user: {
        id: "doc-123",
        firstName: "John",
        lastName: "Smith",
        email: "john.smith@example.com",
        image: "doctor1.jpg",
      },
      specialityName: "Cardiology",
      education: "Harvard Medical School",
      yearsOfExperience: 10,
      about: "Experienced cardiologist specializing in heart health.",
      fees: "150",
      licenseNumber: "LIC12345",
      hospitals: [1],
    });

    const today = new Date("2024-01-16T12:00:00Z");
    const todayStr = "2024-01-16";
    const tomorrowStr = "2024-01-17";

    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);

    const startDate = monday.toISOString().split("T")[0];
    const endDate = sunday.toISOString().split("T")[0];

    mock
      .onGet("http://localhost:8000/api/slot/range/", {
        params: {
          provider: "1",
          start_date: startDate,
          end_date: endDate,
        },
      })
      .reply(200, {
        [todayStr]: [
          {
            id: "slot-1",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "UTC",
            start: "2024-01-16T13:00:00Z",
            end: "2024-01-16T13:30:00Z",
            status: "FREE",
          },
          {
            id: "slot-2",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "UTC",
            start: "2024-01-16T14:00:00Z",
            end: "2024-01-16T14:30:00Z",
            status: "FREE",
          },
        ],
        [tomorrowStr]: [
          {
            id: "slot-3",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "UTC",
            start: "2024-01-17T09:00:00Z",
            end: "2024-01-17T09:30:00Z",
            status: "FREE",
          },
        ],
      });

    renderDoctorsPage("/appointment/1");

    // Wait for doctor details to load
    await waitFor(() => {
      expect(screen.getByText(/John Smith/i)).toBeInTheDocument();
      expect(screen.getByText(/\$150/)).toBeInTheDocument();
    });

    // Wait for slots to load
    await waitFor(() => {
      expect(screen.getByText(/13:00 – 13:30/i)).toBeInTheDocument();
    });

    // Click on an available slot
    const slotButton = screen.getByText(/13:00 – 13:30/i).closest("button");
    expect(slotButton).not.toBeDisabled();
    await user.click(slotButton!);

    // Verify slot is selected (has primary border class)
    await waitFor(() => {
      expect(slotButton).toHaveClass("border-primary");
    });

    // Reason input should appear
    await waitFor(() => {
      expect(screen.getByLabelText(/reason for visit/i)).toBeInTheDocument();
    });

    // Book button should be disabled initially (no reason entered)
    const bookButton = screen.getByRole("button", {
      name: /book appointment/i,
    });
    expect(bookButton).toBeDisabled();

    // Enter reason
    await user.type(
      screen.getByLabelText(/reason for visit/i),
      "Chest pain consultation",
    );

    // Book button should now be enabled
    expect(bookButton).not.toBeDisabled();
  });

  it("should successfully book an appointment", async () => {
    mock.onGet("http://localhost:8000/api/provider/1").reply(200, {
      id: "1",
      user: {
        id: "doc-123",
        firstName: "John",
        lastName: "Smith",
        email: "john.smith@example.com",
        image: "doctor1.jpg",
      },
      specialityName: "Cardiology",
      education: "Harvard Medical School",
      yearsOfExperience: 10,
      about: "Experienced cardiologist specializing in heart health.",
      fees: "150",
      licenseNumber: "LIC12345",
      hospitals: [1],
    });

    const today = new Date("2024-01-16T12:00:00Z");
    const todayStr = "2024-01-16";
    const tomorrowStr = "2024-01-17";

    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);

    const startDate = monday.toISOString().split("T")[0];
    const endDate = sunday.toISOString().split("T")[0];

    mock
      .onGet("http://localhost:8000/api/slot/range/", {
        params: {
          provider: "1",
          start_date: startDate,
          end_date: endDate,
        },
      })
      .reply(200, {
        [todayStr]: [
          {
            id: "slot-1",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: "2024-01-16T13:00:00Z",
            end: "2024-01-16T13:30:00Z",
            status: "FREE",
          },
        ],
        [tomorrowStr]: [
          {
            id: "slot-2",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: "2024-01-17T09:00:00Z",
            end: "2024-01-17T09:30:00Z",
            status: "FREE",
          },
        ],
      });

    mock.onPost("http://localhost:8000/api/appointment/").reply(201, {
      id: "appt-123",
      patientId: "patient-123",
      providerId: "1",
      appointmentStartDatetimeUtc: "2024-01-16T13:00:00Z",
      appointmentEndDatetimeUtc: "2024-01-16T13:30:00Z",
      location: 1,
      reason: "Chest pain consultation",
      status: "REQUESTED",
    });

    renderDoctorsPage("/appointment/1");

    // Wait for doctor details to load
    await waitFor(() => {
      expect(screen.getByText(/John Smith/i)).toBeInTheDocument();
      expect(screen.getByText(/\$150/)).toBeInTheDocument();
    });

    // Wait for slots to load
    await waitFor(() => {
      expect(screen.getByText(/13:00 – 13:30/i)).toBeInTheDocument();
    });

    const slotButton = screen.getByText(/13:00 – 13:30/i).closest("button");
    expect(slotButton).not.toBeDisabled();
    await user.click(slotButton!);

    // Wait for reason input to appear and enter reason
    await waitFor(() => {
      expect(screen.getByLabelText(/reason for visit/i)).toBeInTheDocument();
    });

    await user.type(
      screen.getByLabelText(/reason for visit/i),
      "Chest pain consultation",
    );

    // Book appointment
    const bookButton = screen.getByRole("button", {
      name: /book appointment/i,
    });

    await waitFor(() => {
      expect(bookButton).not.toBeDisabled();
    });

    await user.click(bookButton);

    // Verify success message
    await waitFor(() => {
      expect(
        screen.getByText(/appointment requested successfully/i),
      ).toBeInTheDocument();
    });

    // Verify API was called correctly
    expect(mock.history.post.length).toBe(1);
    expect(mock.history.post[0].url).toBe("/appointment/");

    const appointmentData = JSON.parse(mock.history.post[0].data);
    expect(appointmentData).toMatchObject({
      provider: "1",
      patient: "patient-123",
      reason: "Chest pain consultation",
      appointmentStartDatetimeUtc: "2024-01-16T13:00:00Z",
      appointmentEndDatetimeUtc: "2024-01-16T13:30:00Z",
      location: 1,
    });
  });

  it("should not allow booking without selecting slot or reason", async () => {
    mock.onGet("http://localhost:8000/api/provider/1").reply(200, {
      id: "1",
      user: {
        id: "doc-123",
        firstName: "John",
        lastName: "Smith",
        email: "john.smith@example.com",
        image: "doctor1.jpg",
      },
      specialityName: "Cardiology",
      education: "Harvard Medical School",
      yearsOfExperience: 10,
      about: "Experienced cardiologist specializing in heart health.",
      fees: "150",
      licenseNumber: "LIC12345",
      hospitals: [1],
    });

    const today = new Date("2024-01-16T12:00:00Z");
    const todayStr = "2024-01-16";
    const tomorrowStr = "2024-01-17";

    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);

    const startDate = monday.toISOString().split("T")[0];
    const endDate = sunday.toISOString().split("T")[0];

    mock
      .onGet("http://localhost:8000/api/slot/range/", {
        params: {
          provider: "1",
          start_date: startDate,
          end_date: endDate,
        },
      })
      .reply(200, {
        [todayStr]: [
          {
            id: "slot-1",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: "2024-01-16T13:00:00Z",
            end: "2024-01-16T13:30:00Z",
            status: "FREE",
          },
        ],
        [tomorrowStr]: [
          {
            id: "slot-2",
            hospitalId: 1,
            hospitalName: "City General Hospital",
            hospitalTimezone: "America/New_York",
            start: "2024-01-17T09:00:00Z",
            end: "2024-01-17T09:30:00Z",
            status: "FREE",
          },
        ],
      });

    renderDoctorsPage("/appointment/1");

    // Wait for doctor details to load
    await waitFor(() => {
      expect(screen.getByText(/John Smith/i)).toBeInTheDocument();
      expect(screen.getByText(/\$150/)).toBeInTheDocument();
    });

    // Wait for slots to load
    await waitFor(() => {
      expect(screen.getByText(/13:00 – 13:30/i)).toBeInTheDocument();
    });

    // Book button should be disabled initially (no slot selected)
    const bookButton = screen.getByRole("button", {
      name: /book appointment/i,
    });
    expect(bookButton).toBeDisabled();

    // Select slot with no reason
    const slotButton = screen.getByText(/13:00 – 13:30/i).closest("button");
    expect(slotButton).not.toBeDisabled();
    await user.click(slotButton!);

    // Wait for reason input to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/reason for visit/i)).toBeInTheDocument();
    });

    // Book button should still be disabled (no reason entered)
    expect(bookButton).toBeDisabled();

    await user.type(
      screen.getByLabelText(/reason for visit/i),
      "Chest pain consultation",
    );

    // Book button should now be enabled
    await waitFor(() => {
      expect(bookButton).not.toBeDisabled();
    });
  });

  it("should show related doctors on appointment page", async () => {
    mock.onGet("http://localhost:8000/api/provider/1").reply(200, {
      id: "1",
      user: {
        id: "doc-123",
        firstName: "John",
        lastName: "Smith",
        email: "john.smith@example.com",
        image: "doctor1.jpg",
      },
      specialityName: "Cardiology",
      education: "Harvard Medical School",
      yearsOfExperience: 10,
      about: "Experienced cardiologist specializing in heart health.",
      fees: "150",
      licenseNumber: "LIC12345",
      hospitals: [1],
    });

    // Mock slots data
    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    mock.onGet(/\/slot\/range\/\?provider=.*/).reply((config) => {
      const url = new URL(config.url!, "http://localhost:8000");
      const provider = url.searchParams.get("provider");

      if (provider === "1") {
        return [
          200,
          {
            [todayStr]: [
              {
                id: "slot-1",
                hospitalId: 1,
                hospitalName: "City General Hospital",
                hospitalTimezone: "America/New_York",
                start: `${todayStr}T09:00:00Z`,
                end: `${todayStr}T09:30:00Z`,
                status: "FREE",
              },
            ],
          },
        ];
      }
      return [404, { detail: "Not found" }];
    });

    renderDoctorsPage("/appointment/1");

    // Wait for doctor details to load
    await waitFor(() => {
      expect(screen.getByText(/appointment fee/i)).toBeInTheDocument();
      expect(screen.getByText(/\$150/)).toBeInTheDocument();
    });

    // Verify related doctors section appears
    await waitFor(() => {
      expect(screen.getByText(/top doctors to book/i)).toBeInTheDocument();
    });

    // Should show other cardiologists
    expect(screen.getByText("Peter Doan")).toBeInTheDocument();

    // Should not show the current doctor
    const relatedSection = screen.getByTestId("related-doctors");
    expect(
      within(relatedSection!).queryByText("John Smith"),
    ).not.toBeInTheDocument();

    // Should not show doctors from different specialities
    expect(screen.queryByText("Emily Williams")).not.toBeInTheDocument();
  });
});
