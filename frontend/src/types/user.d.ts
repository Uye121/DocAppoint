export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  dateOfBirth?: string | null;
  phoneNumber?: string | null;
  address?: string | null;
  image?: string | null;
  isActive: boolean;
  hasAdminStaffProfile: boolean;
  hasPatientProfile: boolean;
  hasProviderProfile: boolean;
  hasSystemAdminProfile: boolean;
  userRole: string;
}
