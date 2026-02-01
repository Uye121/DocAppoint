export interface User {
  address?: string | null;
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
