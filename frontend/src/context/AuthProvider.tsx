import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { AuthPayload } from "../types/auth";
import type { User } from "../types/auth";
import {
  login as apiLogin,
  signup as apiSignup,
  logout as apiLogout,
  getMe,
} from "../api/auth";
import { AuthContext } from "./AuthContext";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  useEffect(() => {
    const bootstrap = async () => {
      if (!localStorage.getItem("access")) {
        setLoading(false);
        return;
      }

      try {
        const me = await getMe();
        setUser(me);
      } catch (err) {
        console.log(err);
        localStorage.clear();
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  const login = async (payload: AuthPayload) => {
    const { user, access, refresh } = await apiLogin(payload);
    localStorage.setItem("access", access);
    localStorage.setItem("refresh", refresh);
    setUser(user);
  };

  const signup = async (payload: AuthPayload) => {
    await apiSignup(payload);
    nav("/verify");
  };

  const logout = async () => {
    await apiLogout();
    localStorage.clear();
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const me = await getMe();
      setUser(me);
      return me;
    } catch (err) {
      console.log(err);
      localStorage.clear();
      setUser(null);
      return null;
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, signup, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
};
