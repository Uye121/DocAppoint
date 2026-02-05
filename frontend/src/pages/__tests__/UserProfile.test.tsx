import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import UserProfile from "../UserProfile";
import { useAuth } from "../../../hooks/useAuth";
import { getPatientInfo, updatePatientInfo } from "../../api/patient";
import type { PatientDetail } from "../../types/patient";
import type { User } from "../../types/user";
import type { AuthCtx } from "../../types/auth";

vi.mock("../../../hooks/useAuth");
vi.mock("../../api/patient");
vi.mock("../../assets/assets_frontend/assets", () => ({
  assets: {
    profile_pic: "profile.jpg",
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter>
    <QueryClientProvider client={createTestQueryClient()}>
      {children}
    </QueryClientProvider>
  </MemoryRouter>
);

const mockUser: User = {
  id: "1",
  email: "john.doe@example.com",
  firstName: "John",
  lastName: "Doe",
  phoneNumber: "123-456-7890",
  addressLine1: "123 Main St",
  addressLine2: "Apt 4B",
  city: "New York",
  state: "NY",
  zipCode: "10001",
  dateOfBirth: "1990-01-01",
  userName: "johndoe",
  hasAdminStaffProfile: false,
  hasPatientProfile: true,
  hasProviderProfile: false,
  hasSystemAdminProfile: false,
  userRole: "patient",
};

const mockPatientData: PatientDetail = {
  user: mockUser,
  bloodType: "O+",
  allergies: "Peanuts, Penicillin",
  chronicConditions: "Asthma",
  currentMedications: "Albuterol, Fluticasone",
  insurance: "Blue Shield",
  height: 175,
  weight: 70,
};

describe("UserProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1" },
      loading: false,
    } as AuthCtx);
    vi.mocked(getPatientInfo).mockResolvedValue(mockPatientData);
    vi.mocked(updatePatientInfo).mockResolvedValue(mockPatientData);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows spinner while loading", () => {
    vi.mocked(getPatientInfo).mockImplementation(() => new Promise(() => {}));

    render(<UserProfile />, { wrapper: TestWrapper });
    expect(screen.getByText(/Loading profile information/)).toBeInTheDocument();
  });

  it("displays user profile information correctly", async () => {
    render(<UserProfile />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    // Contact Information
    const emailElements = screen.getAllByText("john.doe@example.com");
    expect(emailElements.length).toBeGreaterThan(0);
    expect(screen.getByText("123-456-7890")).toBeInTheDocument();
    expect(screen.getByText(/123 Main St/)).toBeInTheDocument();
    expect(screen.getByText(/Apt 4B/)).toBeInTheDocument();
    expect(screen.getByText(/New York, New York, 10001/)).toBeInTheDocument();

    // Basic Information
    expect(screen.getByText("January 1, 1990")).toBeInTheDocument();

    // Medical Information
    expect(screen.getByText("O+")).toBeInTheDocument();
    expect(screen.getByText("Peanuts, Penicillin")).toBeInTheDocument();
    expect(screen.getByText("Asthma")).toBeInTheDocument();
    expect(screen.getByText("Albuterol, Fluticasone")).toBeInTheDocument();
    expect(screen.getByText("Blue Shield")).toBeInTheDocument();
    expect(screen.getByText("175 cm")).toBeInTheDocument();
    expect(screen.getByText("70 kg")).toBeInTheDocument();
  });

  it("shows 'Not provided' for empty fields", async () => {
    const emptyData: PatientDetail = {
      user: {
        ...mockUser,
        phoneNumber: "",
        addressLine1: "",
        addressLine2: "",
        city: "",
        state: "",
        zipCode: "",
        dateOfBirth: "",
      },
      bloodType: "",
      allergies: "",
      chronicConditions: "",
      currentMedications: "",
      insurance: "",
      height: undefined,
      weight: undefined,
    };

    vi.mocked(getPatientInfo).mockResolvedValue(emptyData);

    render(<UserProfile />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    expect(screen.getAllByText("Not provided")).toHaveLength(7);
    expect(screen.getAllByText("None reported")).toHaveLength(3);
  });

  it("enters edit mode when Edit button is clicked", async () => {
    render(<UserProfile />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    const editButton = screen.getByRole("button", { name: /Edit Profile/i });
    fireEvent.click(editButton);

    expect(screen.getByPlaceholderText("First name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Last name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("(123) 456-7890")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Street address")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Apt, suite, etc. (optional)"),
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("City")).toBeInTheDocument();

    // Check city input value
    const cityInput = screen.getByPlaceholderText("City");
    expect(cityInput).toHaveValue("New York");

    // Check state select has correct value selected
    const stateSelect = screen.getByRole("combobox");
    expect(stateSelect).toBeInTheDocument();
    expect(stateSelect.tagName).toBe("SELECT");
    expect(stateSelect).toHaveValue("NY");

    expect(screen.getByPlaceholderText("ZIP Code")).toBeInTheDocument();
    const zipInput = screen.getByPlaceholderText("ZIP Code");
    expect(zipInput).toHaveValue("10001");

    // Should show Save and Cancel buttons
    expect(
      screen.getByRole("button", { name: /Save Changes/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
  });

  it("allows updating user information in edit mode", async () => {
    render(<UserProfile />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Edit Profile/i }));

    // Update fields
    const firstNameInput = screen.getByPlaceholderText("First name");
    const phoneInput = screen.getByPlaceholderText("(123) 456-7890");
    const cityInput = screen.getByPlaceholderText("City");
    const streetAddress1 = screen.getByPlaceholderText("Street address");
    const streetAddress2 = screen.getByPlaceholderText(
      "Apt, suite, etc. (optional)",
    );
    const zipCode = screen.getByPlaceholderText("ZIP Code");
    const bloodType = screen.getByPlaceholderText("e.g., O+");
    const allergies = screen.getByPlaceholderText("List any allergies");
    const chronicCond = screen.getByPlaceholderText(
      "List any chronic conditions",
    );
    const meds = screen.getByPlaceholderText("List current medications");
    const insurance = screen.getByPlaceholderText("e.g., Blue Shield");

    fireEvent.change(firstNameInput, { target: { value: "Jonathan" } });
    fireEvent.change(phoneInput, { target: { value: "555-123-4567" } });
    fireEvent.change(cityInput, { target: { value: "Los Angeles" } });
    fireEvent.change(streetAddress1, { target: { value: "9 Spring St" } });
    fireEvent.change(streetAddress2, { target: { value: "Suite 100" } });
    fireEvent.change(zipCode, { target: { value: "90005" } });
    fireEvent.change(bloodType, { target: { value: "A" } });
    fireEvent.change(allergies, { target: { value: "Red meat" } });
    fireEvent.change(chronicCond, { target: { value: "Back pain" } });
    fireEvent.change(meds, { target: { value: "Tylenol" } });
    fireEvent.change(insurance, { target: { value: "Blue shield" } });

    const saveButton = screen.getByRole("button", { name: /Save Changes/i });
    fireEvent.click(saveButton);

    // Should call updatePatientInfo with updated data
    await waitFor(() => {
      expect(updatePatientInfo).toHaveBeenCalledWith(
        "1",
        expect.objectContaining({
          user: expect.objectContaining({
            firstName: "Jonathan",
            phoneNumber: "555-123-4567",
            city: "Los Angeles",
            addressLine1: "9 Spring St",
            addressLine2: "Suite 100",
            zipCode: "90005",
          }),
          bloodType: "A",
          allergies: "Red meat",
          chronicConditions: "Back pain",
          currentMedications: "Tylenol",
          insurance: "Blue shield",
        }),
      );
    });
  });

  it("cancels edit mode without saving", async () => {
    render(<UserProfile />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Edit Profile/i }));

    const firstNameInput = screen.getByPlaceholderText("First name");
    fireEvent.change(firstNameInput, { target: { value: "Jonathan" } });

    // Click cancel
    const cancelButton = screen.getByRole("button", { name: /Cancel/i });
    fireEvent.click(cancelButton);

    // Should exit edit mode and show original data
    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Edit Profile/i }),
      ).toBeInTheDocument();
    });

    expect(updatePatientInfo).not.toHaveBeenCalled();
  });

  it("shows state dropdown with options in edit mode", async () => {
    render(<UserProfile />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Edit Profile/i }));

    const stateSelect = screen.getByRole("combobox");
    expect(stateSelect).toBeInTheDocument();
    expect(stateSelect).toHaveValue("NY");

    expect(screen.getByText("California")).toBeInTheDocument();
    expect(screen.getByText("New York")).toBeInTheDocument();
    expect(screen.getByText("Texas")).toBeInTheDocument();
  });

  it("handles API errors gracefully", async () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    vi.mocked(getPatientInfo).mockRejectedValue(new Error("Failed to load"));

    // Render should not throw
    expect(() => {
      render(<UserProfile />, { wrapper: TestWrapper });
    }).not.toThrow();

    await waitFor(
      () => {
        expect(
          screen.getByRole("button", { name: /Edit Profile/i }),
        ).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    consoleError.mockRestore();
  });
});
