export interface User {
  addressLine1?: string | null;
  addressLine2?: string | null;
  city?: string;
  state?: string;
  zipCode?: string;
  dateOfBirth?: string | null;
  email: string;
  firstName: string;
  hasAdminStaffProfile: boolean;
  hasPatientProfile: boolean;
  hasProviderProfile: boolean;
  hasSystemAdminProfile: boolean;
  id: string;
  image?: string | null;
  lastName: string;
  phoneNumber?: string | null;
  userRole: "unassigned" | "patient" | "provider";
  userName: string;
}
