import { useNavigate } from "react-router-dom";
import axios from "axios";

import {
  login as apiLogin,
  signup as apiSignup,
  passwordReset,
  passwordResetConfirm
} from "../src/api/auth";
import type { AuthPayload, PasswordResetConfirmPayload } from "../src/types/auth";

export const useAuth = () => {
  const nav = useNavigate();

  const login = async (payload: AuthPayload) => {
    const { user, access, refresh } = await apiLogin(payload);
    localStorage.setItem("access", access);
    localStorage.setItem("refresh", refresh);
    nav("/");
    return user;
  };

  const signup = async (payload: AuthPayload) => {
    await apiSignup(payload);
    nav("/verify");
  };

  const logout = () => {
    localStorage.clear();
    nav("/login");
  };

//   const resetPassword = async (email: string) => {
//     await passwordReset({ email });
//     nav('/reset-password-sent');
//   };

//   const confirmReset = async (payload: PasswordResetConfirmPayload) => {
//     await passwordResetConfirm(payload);
//     nav('/login');
//   }
// ;
  return { login, signup, logout };
};
