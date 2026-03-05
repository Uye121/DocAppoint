import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import {
  AuthProvider,
  SpecialitiesProvider,
  DoctorProvider,
} from "../../src/context";
import { UserProfile, Login, Home } from "../../src/pages";
import { ProtectedRoutes } from "../../src/components";
import { mock } from "../server";

describe("Patient Profile Management Flow", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  const renderProfilePage = (
    initialPath = "/user-profile",
    userMock?: () => [number, unknown],
    patientMock?: () => [number, unknown],
  ) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Mock authenticated user
    if (userMock) {
      mock.onGet("http://localhost:8000/api/users/me").reply(userMock);
    } else {
      mock.onGet("http://localhost:8000/api/users/me").reply(200, {
        id: "patient-123",
        email: "patient@example.com",
        firstName: "John",
        lastName: "Doe",
        userRole: "patient",
        userName: "johndoe",
        phoneNumber: "555-123-4567",
        addressLine1: "123 Main St",
        addressLine2: "Apt 4B",
        city: "Boston",
        state: "MA",
        zipCode: "02108",
        dateOfBirth: "1990-01-01",
        hasPatientProfile: true,
        hasProviderProfile: false,
        hasAdminStaffProfile: false,
        hasSystemAdminProfile: false,
      });
    }

    // Mock patient info
    if (patientMock) {
      mock.onGet("http://localhost:8000/api/patient/me").reply(patientMock);
    } else {
      mock.onGet("http://localhost:8000/api/patient/me").reply(200, {
        user: {
          id: "patient-123",
          email: "patient@example.com",
          firstName: "John",
          lastName: "Doe",
          phoneNumber: "555-123-4567",
          addressLine1: "123 Main St",
          addressLine2: "Apt 4B",
          city: "Boston",
          state: "MA",
          zipCode: "02108",
          dateOfBirth: "1990-01-01",
        },
        bloodType: "O+",
        allergies: "Pollen, Peanuts",
        chronicConditions: "Asthma",
        currentMedications: "Inhaler, Allegra",
        insurance: "Blue Cross",
        weight: 70,
        height: 175,
      });
    }

    // Set tokens
    localStorage.setItem("access", "valid-token");
    localStorage.setItem("refresh", "valid-refresh");

    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<div>Home Page</div>} />
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
                  <Route path="/user-profile" element={<UserProfile />} />
                  <Route path="/patient-home" element={<Home />} />
                </Route>
              </Route>
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  };

  it("should display user profile information", async () => {
    renderProfilePage("/user-profile");

    // Wait for profile to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Check contact information
    const emailElements = await screen.findAllByText("patient@example.com");
    expect(emailElements.length).toBeGreaterThan(0);
    expect(screen.getByText("555-123-4567")).toBeInTheDocument();

    // Check address - match the actual format
    const addressElement = screen.getByText(/123 Main St/).parentElement;
    expect(addressElement).toHaveTextContent("123 Main St");
    expect(addressElement).toHaveTextContent("Apt 4B");
    expect(addressElement).toHaveTextContent("Boston, Massachusetts, 02108");

    // Check basic information
    expect(screen.getByText("January 1, 1990")).toBeInTheDocument();

    // Check medical information
    expect(screen.getByText("O+")).toBeInTheDocument();
    expect(screen.getByText("Pollen, Peanuts")).toBeInTheDocument();
    expect(screen.getByText("Asthma")).toBeInTheDocument();
    expect(screen.getByText("Inhaler, Allegra")).toBeInTheDocument();
    expect(screen.getByText("Blue Cross")).toBeInTheDocument();
    expect(screen.getByText("175 cm")).toBeInTheDocument();
    expect(screen.getByText("70 kg")).toBeInTheDocument();
  });

  it("should enter edit mode when clicking Edit Profile", async () => {
    renderProfilePage("/user-profile");

    // Wait for profile to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    // Verify edit mode - form fields should appear
    await waitFor(() => {
      // Contact fields should be editable
      expect(screen.getByDisplayValue("John")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Doe")).toBeInTheDocument();
      expect(screen.getByDisplayValue("555-123-4567")).toBeInTheDocument();
      expect(screen.getByDisplayValue("123 Main St")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Apt 4B")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Boston")).toBeInTheDocument();

      const stateSelect = screen.getByRole("combobox");
      expect(stateSelect).toBeInTheDocument();

      const selectedOption = Array.from(
        stateSelect.querySelectorAll("option"),
      ).find((option) => option.selected);
      expect(selectedOption).toHaveValue("MA");
      expect(selectedOption).toHaveTextContent("Massachusetts");

      expect(screen.getByDisplayValue("02108")).toBeInTheDocument();

      // Medical fields should be editable
      expect(screen.getByDisplayValue("O+")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Pollen, Peanuts")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Asthma")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Inhaler, Allegra")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Blue Cross")).toBeInTheDocument();
      expect(screen.getByDisplayValue("175")).toBeInTheDocument();
      expect(screen.getByDisplayValue("70")).toBeInTheDocument();
    });

    // Save and Cancel buttons should appear
    expect(
      screen.getByRole("button", { name: /save changes/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("should update profile information successfully", async () => {
    // Mock successful profile update
    mock.onPatch("http://localhost:8000/api/patient/patient-123/").reply(200, {
      user: {
        firstName: "Jonathan",
        lastName: "Smith",
        phoneNumber: "555-999-8888",
      },
      bloodType: "A+",
      allergies: "None",
      chronicConditions: "None",
      currentMedications: "None",
      weight: 75,
      height: 180,
    });

    renderProfilePage("/user-profile");

    // Wait for profile to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    await waitFor(() => {
      expect(screen.getByDisplayValue("John")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Doe")).toBeInTheDocument();
    });

    // Update form fields
    const firstNameInput = screen.getByDisplayValue("John");
    await user.clear(firstNameInput);
    await user.type(firstNameInput, "Jonathan");

    const lastNameInput = screen.getByDisplayValue("Doe");
    await user.clear(lastNameInput);
    await user.type(lastNameInput, "Smith");

    const phoneInput = screen.getByDisplayValue("555-123-4567");
    await user.clear(phoneInput);
    await user.type(phoneInput, "555-999-8888");

    const bloodTypeInput = screen.getByDisplayValue("O+");
    await user.clear(bloodTypeInput);
    await user.type(bloodTypeInput, "A+");

    const allergiesInput = screen.getByDisplayValue("Pollen, Peanuts");
    await user.clear(allergiesInput);
    await user.type(allergiesInput, "None");

    const chronicConditionsInput = screen.getByDisplayValue("Asthma");
    await user.clear(chronicConditionsInput);
    await user.type(chronicConditionsInput, "None");

    const medicationsInput = screen.getByDisplayValue("Inhaler, Allegra");
    await user.clear(medicationsInput);
    await user.type(medicationsInput, "None");

    const weightInput = screen.getByDisplayValue("70");
    await user.clear(weightInput);
    await user.type(weightInput, "75");

    const heightInput = screen.getByDisplayValue("175");
    await user.clear(heightInput);
    await user.type(heightInput, "180");

    // Save changes
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    // Verify API was called with updated data
    await waitFor(() => {
      expect(mock.history.patch.length).toBe(1);
      const requestData = JSON.parse(mock.history.patch[0].data);

      expect(requestData.user).toMatchObject({
        firstName: "Jonathan",
        lastName: "Smith",
        phoneNumber: "555-999-8888",
      });

      // Check medical fields at root level
      expect(requestData).toMatchObject({
        bloodType: "A+",
        allergies: "None",
        chronicConditions: "None",
        currentMedications: "None",
        weight: 75,
        height: 180,
      });
    });

    // Verify UI updates in VIEW MODE (not edit mode)
    await waitFor(() => {
      expect(screen.getByText("Jonathan Smith")).toBeInTheDocument();
      expect(screen.getByText("555-999-8888")).toBeInTheDocument();
      expect(screen.getByText("A+")).toBeInTheDocument();
      expect(screen.getAllByText("None")).toHaveLength(3);
      expect(screen.getByText("180 cm")).toBeInTheDocument();
      expect(screen.getByText("75 kg")).toBeInTheDocument();
    });

    // Edit button should reappear (confirming we're back in view mode)
    expect(
      screen.getByRole("button", { name: /edit profile/i }),
    ).toBeInTheDocument();
  });

  it("should cancel editing and revert changes", async () => {
    renderProfilePage("/user-profile");

    // Wait for profile to load in view mode
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    // Wait for form fields to appear
    await waitFor(() => {
      expect(screen.getByDisplayValue("John")).toBeInTheDocument();
      expect(screen.getByDisplayValue("O+")).toBeInTheDocument();
    });

    // Store references to inputs before modifying
    const firstNameInput = screen.getByDisplayValue("John");
    const bloodTypeInput = screen.getByDisplayValue("O+");

    // Modify some fields
    await user.clear(firstNameInput);
    await user.type(firstNameInput, "Jonathan");

    await user.clear(bloodTypeInput);
    await user.type(bloodTypeInput, "B-");

    // Verify inputs show modified values
    expect(screen.getByDisplayValue("Jonathan")).toBeInTheDocument();
    expect(screen.getByDisplayValue("B-")).toBeInTheDocument();

    // Click cancel
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    // Wait for view mode to reappear with original values
    await waitFor(() => {
      // Should be back in view mode (no input fields)
      expect(screen.queryByDisplayValue("Jonathan")).not.toBeInTheDocument();
      expect(screen.queryByDisplayValue("B-")).not.toBeInTheDocument();

      // Original values should be displayed as text
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(screen.getByText("O+")).toBeInTheDocument();
    });

    // Verify edit button is back
    expect(
      screen.getByRole("button", { name: /edit profile/i }),
    ).toBeInTheDocument();

    // Verify no API call was made
    expect(mock.history.patch.length).toBe(0);
  });

  it("should validate numeric fields (weight and height)", async () => {
    renderProfilePage("/user-profile");

    // Wait for profile to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    // Wait for form fields to appear
    await waitFor(() => {
      expect(screen.getByDisplayValue("70")).toBeInTheDocument();
      expect(screen.getByDisplayValue("175")).toBeInTheDocument();
    });

    // Get input fields
    const weightInput = screen.getByDisplayValue("70");
    const heightInput = screen.getByDisplayValue("175");

    // Try to enter non-numeric values
    await user.clear(weightInput);
    await user.type(weightInput, "abc");

    await user.clear(heightInput);
    await user.type(heightInput, "xyz");

    // Number inputs with non-numeric values become null
    expect(weightInput).toHaveValue(null);
    expect(heightInput).toHaveValue(null);

    // Clear and enter valid numbers
    await user.clear(weightInput);
    await user.type(weightInput, "80");

    await user.clear(heightInput);
    await user.type(heightInput, "185");

    // Should accept valid numbers
    await waitFor(() => {
      expect(weightInput).toHaveValue(80);
      expect(heightInput).toHaveValue(185);
    });

    // Verify input types
    expect(weightInput).toHaveAttribute("type", "number");
    expect(heightInput).toHaveAttribute("type", "number");
  });

  it("should handle API errors during profile update", async () => {
    // Mock failed update
    mock.onPatch("http://localhost:8000/api/patient/patient-123/").reply(500, {
      detail: "Server error",
    });

    renderProfilePage("/user-profile");

    // Wait for profile to load in view mode
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    // Wait for form fields to appear
    await waitFor(() => {
      expect(screen.getByDisplayValue("O+")).toBeInTheDocument();
    });

    // Update a field
    const bloodTypeInput = screen.getByDisplayValue("O+");
    await user.clear(bloodTypeInput);
    await user.type(bloodTypeInput, "B-");

    // Verify the input was updated
    expect(screen.getByDisplayValue("B-")).toBeInTheDocument();

    // Save changes
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    // Verify error message content (adjust based on your error display)
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/server error|failed|error/i);

    // Should stay in edit mode (form fields still visible with edited value)
    expect(screen.getByDisplayValue("B-")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /save changes/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();

    // Verify no navigation occurred (still on profile page)
    expect(screen.getByText(/contact information/i)).toBeInTheDocument();
  });

  it("should allow partial updates", async () => {
    // Mock successful partial update
    mock.onPatch("http://localhost:8000/api/patient/patient-123/").reply(200, {
      user: {
        phoneNumber: "555-777-1234",
      },
    });

    renderProfilePage("/user-profile");

    // Wait for profile to load in view mode
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole("button", { name: /edit profile/i });
    await user.click(editButton);

    // Wait for form fields to appear
    await waitFor(() => {
      expect(screen.getByDisplayValue("555-123-4567")).toBeInTheDocument();
    });

    // Only update phone number
    const phoneInput = screen.getByDisplayValue("555-123-4567");
    await user.clear(phoneInput);
    await user.type(phoneInput, "555-777-1234");

    // Save changes
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    // Verify API was called with ALL current data (including unchanged fields)
    await waitFor(() => {
      expect(mock.history.patch.length).toBe(1);
      const requestData = JSON.parse(mock.history.patch[0].data);

      // Phone number should be updated in the nested user object
      expect(requestData.user?.phoneNumber).toBe("555-777-1234");

      // Other fields should still be present (not undefined)
      expect(requestData.user?.firstName).toBe("John");
      expect(requestData.user?.lastName).toBe("Doe");
      expect(requestData.bloodType).toBe("O+");
    });

    // Wait for view mode to return
    await waitFor(() => {
      expect(
        screen.queryByDisplayValue("555-777-1234"),
      ).not.toBeInTheDocument();
    });

    // Phone number should be updated in view mode
    expect(screen.getByText("555-777-1234")).toBeInTheDocument();

    // Other fields should remain unchanged
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("O+")).toBeInTheDocument();

    // Edit button should be back
    expect(
      screen.getByRole("button", { name: /edit profile/i }),
    ).toBeInTheDocument();
  });

  it("should redirect to login if not authenticated", async () => {
    localStorage.clear();

    renderProfilePage("/user-profile", () => [401, { detail: "Unauthorized" }]);

    // Should redirect to login
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /login/i }),
      ).toBeInTheDocument();
    });
  });

  it("should show empty states for missing information", async () => {
    renderProfilePage(
      "/user-profile",
      () => [
        200,
        {
          id: "patient-123",
          email: "patient@example.com",
          firstName: "John",
          lastName: "Doe",
          userRole: "patient",
          userName: "johndoe",
        },
      ],
      () => [
        200,
        {
          user: {
            id: "patient-123",
            email: "patient@example.com",
            firstName: "John",
            lastName: "Doe",
          },
        },
      ],
    );

    // Wait for profile to load
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Contact Information
    const phoneNumberElement = screen
      .getByText("Phone Number")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-primary");
    expect(phoneNumberElement).toHaveTextContent("Not provided");

    // Address - find the div with whitespace-pre-line class
    const addressElement = screen
      .getByText("Address")
      .closest("div")
      ?.querySelector("div.whitespace-pre-line");
    expect(addressElement).toHaveTextContent("Not provided");

    // Basic Information
    const dobElement = screen
      .getByText("Date of Birth")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(dobElement).toHaveTextContent("Not provided");

    // Medical Information
    const bloodTypeElement = screen
      .getByText("Blood Type")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(bloodTypeElement).toHaveTextContent("Not provided");

    const allergiesElement = screen
      .getByText("Allergies")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(allergiesElement).toHaveTextContent("None reported");

    const chronicElement = screen
      .getByText("Chronic Conditions")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(chronicElement).toHaveTextContent("None reported");

    const medicationsElement = screen
      .getByText("Current Medications")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(medicationsElement).toHaveTextContent("None reported");

    const insuranceElement = screen
      .getByText("Insurance Provider")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(insuranceElement).toHaveTextContent("Not provided");

    const heightElement = screen
      .getByText("Height (cm)")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(heightElement).toHaveTextContent("Not provided");

    const weightElement = screen
      .getByText("Weight (kg)")
      .closest("div")
      ?.querySelector("p.text-zinc-400, p.text-zinc-700");
    expect(weightElement).toHaveTextContent("Not provided");

    // Verify email is still displayed (required field)
    const emailElements = await screen.findAllByText("patient@example.com");
    expect(emailElements.length).toBeGreaterThan(0);
  });
});
