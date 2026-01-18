import { api } from "./axios";
import type {
  AuthPayload,
  TokenPair,
  ResendVerifyPayload,
  PasswordResetPayload,
  PasswordResetConfirmPayload,
  User,
} from "../types/auth";

export const login = (payload: AuthPayload) =>
  api
    .post<{ user: User } & TokenPair>("/auth/login/", payload)
    .then((res) => res.data);

export const signup = (payload: AuthPayload) =>
  api.post("/users/", payload).then((res) => res.data);

export const verifyEmail = (token: string) =>
  api
    .get<{ detail: string }>(`/auth/verify/?token=${token}`)
    .then((res) => res.data);

export const resendVerify = (payload: ResendVerifyPayload) =>
  api.post("/auth/resend-verify/", payload).then((res) => res.data);

export const passwordReset = (payload: PasswordResetPayload) =>
  api.post("/auth/password-reset/", payload).then((res) => res.data);

export const passwordResetConfirm = (payload: PasswordResetConfirmPayload) =>
  api.post("/auth/password-reset/confirm/", payload).then((res) => res.data);

export const logout = () => {
  const refresh = localStorage.getItem("refresh");
  if (refresh) {
    return api.post("/auth/logout/", { refresh }).then((res) => res.data);
  }
  return Promise.resolve();
};

// Interceptor included the access token in header, so no need to pass it
export const getMe = () => api.get<User>("/auth/me/").then((res) => res.data);
