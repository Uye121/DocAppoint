export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface ResendVerifyPayload {
  email: string;
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