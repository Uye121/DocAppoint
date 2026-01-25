import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { SyncLoader } from "react-spinners";

import type { ResendVerifyPayload } from "../types/auth";
import { VERIFY_STATUS, type VerifyStatus } from "../types/auth";
import { verifyEmail, resendVerify } from "../api/auth";

const VerifyEmail = (): React.JSX.Element => {
  const [searchParams] = useSearchParams();
  const nav = useNavigate();
  const [status, setStatus] = useState<VerifyStatus>(VERIFY_STATUS.LOADING);
  const [email, setEmail] = useState<ResendVerifyPayload | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus(VERIFY_STATUS.FAILURE);
    } else {
      verifyEmail(token)
        .then(() => setStatus(VERIFY_STATUS.SUCCESSFUL))
        .catch(() => setStatus(VERIFY_STATUS.FAILURE));
    }
  }, [searchParams]);

  const renderContent = (status: VerifyStatus) => {
    switch (status) {
      case VERIFY_STATUS.LOADING:
        return (
          <div className="flex flex-col items-center">
            <SyncLoader size={30} color="#38BDF8" loading />
            <p className="mt-4 text-zinc-600">Verifying your email...</p>
          </div>
        );
      case VERIFY_STATUS.SUCCESSFUL:
        return (
          <div className="flex flex-col items-center">
            <h2 className="text-2xl font-semibold mb-2">Email confirmed!</h2>
            <button
              className="border px-10 md:px-16 py-8 mb-4 hover:bg-sky-400 hover:text-white"
              onClick={() => nav("/login")}
            >
              Go to Login
            </button>
          </div>
        );
      case VERIFY_STATUS.FAILURE:
      default:
        return (
          <div className="min-h-screen flex items-center justify-center bg-white">
            <div className="w-full max-w-md px-6 py-12">
              <div className="flex flex-col items-center text-center">
                <h2 className="text-2xl font-semibold mb-2">
                  Invalid or expired link
                </h2>
                <p className="text-zinc-600 mb-6">
                  Please request a new confirmation email.
                </p>

                <div className="w-full mb-5">
                  <label
                    htmlFor="email"
                    className="block text-sm text-zinc-700 mb-1"
                  >
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    name="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="border border-zinc-300 rounded w-full px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
                  />
                </div>
                <button
                  onClick={() => {
                    resendVerify({ email });
                    nav("/verify");
                  }}
                  className="w-full bg-sky-500 text-white py-2.5 rounded hover:bg-sky-600 transition mb-3"
                >
                  Resend Verification Email
                </button>
                <button
                  onClick={() => nav("/login")}
                  className="w-full border border-sky-500 text-sky-500 py-2.5 rounded hover:bg-sky-50 transition"
                >
                  Go to login
                </button>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-8 flex-col text-center max-w-sm">
        {renderContent(status)}
      </div>
    </div>
  );
};

export default VerifyEmail;
