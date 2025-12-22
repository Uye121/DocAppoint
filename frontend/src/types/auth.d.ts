export interface AuthPayload {
  email: string;
  password: string;
  username?: string;
  firstName?: string;
  lastName?: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface ResendVerifyPayload {
  uid: string;
}

export interface PasswordResetPayload {
  email: string;
}

export interface PasswordResetConfirmPayload {
  token: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
}

const VERIFY_STATUS = {
  LOADING: 'Loading',
  FAILURE: 'Failure',
  SUCCESSFUL: 'Successful',
} as const;
type VerifyStatus = typeof VERIFY_STATUS[keyof typeof VERIFY_STATUS];