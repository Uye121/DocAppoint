import axios from "axios";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import { formatErrors } from "../../utils/errorMap";
import type { AuthPayload } from "../types/auth";

const Signup = (): React.JSX.Element => {
  const nav = useNavigate();
  const { signup } = useAuth();
  const [form, setForm] = useState<AuthPayload>({
    email: "",
    password: "",
    username: "",
    firstName: "",
    lastName: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRedirect = () => {
    nav("/login");
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [event.target.name]: event.target.value });

  const handleSubmit = async (event: React.SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);

    try {
      await signup(form);
      nav("/verify");
    } catch (err) {
      console.log(err);

      if (axios.isAxiosError(err)) {
        const errorMsg =
          err.response?.data?.detail || formatErrors(err.response?.data);
        setError(errorMsg);
      } else if (err instanceof Error) {
        setError(err?.message);
      } else {
        setError("Unexpected error occurred");
      }
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="min-h-[80vh] flex items-center">
      <div className="flex flex-col gap-3 m-auto items-start p-8 min-w-[340px] sm:min-w-96 max-w-md border rounded-xl text-zinc-600 text-sm shadow-lg">
        {error && (
          <div
            className="w-full max-w-full text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2"
            role="alert"
          >
            {error}
          </div>
        )}
        <h2 className="text-2xl font-semibold">Create Account</h2>
        <div className="w-full">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            name="username"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.username}
            required
          />
        </div>
        <div className="w-full">
          <label htmlFor="firstName">First Name</label>
          <input
            id="firstName"
            type="text"
            name="firstName"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.firstName}
            required
          />
        </div>
        <div className="w-full">
          <label htmlFor="lastName">Last Name</label>
          <input
            id="lastName"
            type="text"
            name="lastName"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={handleChange}
            value={form.lastName}
            required
          />
        </div>
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
          Create Account
        </button>
        <p>
          Already have an account? Login{" "}
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

export default Signup;
