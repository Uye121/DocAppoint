import { api } from "./axios";
import type {
    AuthPayload,
    TokenPair,
    ResendVerifyPayload,
    PasswordResetPayload,
    PasswordResetConfirmPayload,
    User
} from "../types/auth";

export const login = (payload: AuthPayload) =>
    api.post<{ user: User } & TokenPair>("/login/", payload).then((res) => res.data);

export const signup = async (payload: AuthPayload) => {
    const res = await api.post("/signup/", payload)
    return res.data;
}

export const verifyEmail = (key: string) =>
    api.get<{ detail: string }>(`/verify/${key}`).then((res) => res.data);

export const resendVerify = (payload: ResendVerifyPayload) =>
    api.post("/resend-verify/", payload).then((res) => res.data);

export const passwordReset = (payload: PasswordResetPayload) =>
  api.post("/password-reset/", payload).then((res) => res.data);

export const passwordResetConfirm = (payload: PasswordResetConfirmPayload) =>
  api.post("/password-reset/confirm/", payload).then((res) => res.data);

export const logout = () => {
    const refresh = localStorage.getItem("refresh");
    if (refresh) {
        return api.post("/logout/", { refresh }).then((res) => res.data);
    }
    return Promise.resolve();
}
