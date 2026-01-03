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

export interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (payload: AuthPayload) => Promise<void>;
  signup: (payload: AuthPayload) => Promise<void>;
  logout: () => Promise<void>;
}
