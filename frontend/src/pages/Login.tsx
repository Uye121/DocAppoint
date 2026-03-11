import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../utils/errorMap";
import type { AuthPayload } from "../types/auth";

const Login = (): React.JSX.Element => {
  const nav = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState<AuthPayload>({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);

  const handleRedirect = () => {
    nav("/signup");
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: React.SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);

    try {
      await login(form);
      nav("/");
    } catch (err) {
      toast.error(getErrorMessage(err, "Network error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="min-h-[80vh] flex items-center"
      data-testid="login-page"
    >
      <div className="flex flex-col gap-3 m-auto items-start p-8 min-w-85 sm:min-w-96 max-w-md border rounded-xl text-zinc-600 text-sm shadow-lg">
        <h2 className="text-2xl font-semibold">Login</h2>
        <div className="w-full">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            name="email"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.email}
            required
          />
        </div>
        <div className="w-full">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            name="password"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.password}
            required
          />
        </div>
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
