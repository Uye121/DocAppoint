import axios from "axios";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { formatErrors } from "../../utils/errorMap";
import type { AuthPayload } from "../types/auth";

const Login = (): React.JSX.Element => {
  const nav = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState<AuthPayload>({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRedirect = () => {
    nav("/signup");
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [event.target.name]: event.target.value });

  const handleSubmit = async (event: React.SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);

    try {
      await login(form);
      nav('/');
    } catch (err) {
      console.log(err);

      if (axios.isAxiosError(err) && err.response?.status === 400) {
        const errorMsg =
          err.response?.data?.detail || formatErrors(err.response?.data);
        setError(errorMsg);
      } else if (err instanceof Error) {
        setError(err?.message);
      } else {
        setError("Unexpected error");
      }
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="min-h-[80vh] flex items-center">
      <div className="flex flex-col gap-3 m-auto items-start p-8 min-w-[340px] sm:min-w-96 max-w-md border rounded-xl text-zinc-600 text-sm shadow-lg">
        <p className="text-2xl font-semibold">Login</p>
        <p>Please sign up/login to get started.</p>
        <div className="w-full">
          <p>Email</p>
          <input
            type="email"
            name="email"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.email}
            required
          />
        </div>
        <div className="w-full">
          <p>Password</p>
          <input
            type="password"
            name="password"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.password}
            required
          />
        </div>
        {error && (
          <div
            className="w-full max-w-full text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2"
            role="alert"
          >
            {error}
          </div>
        )}
        <button
          disabled={loading}
          type="submit"
          className="bg-primary text-white w-full py-2 rounded-md text-base"
        >
          Login
        </button>
        <p>
          Create a new account{" "}
          <span
            onClick={handleRedirect}
            className="text-primary underline cursor-pointer"
          >
            here
          </span>
          .
        </p>
      </div>
    </form>
  );
};

export default Login;
