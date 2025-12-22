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
  const [uid, setUid] = useState<ResendVerifyPayload | null>(null);

  useEffect(() => {
    const uid = searchParams.get("uid");
    const token = searchParams.get("token");

    if (!uid || !token) {
      setStatus(VERIFY_STATUS.FAILURE);
      return;
    }

    setUid({ uid });
    const key = `${uid}-${token}`;
    verifyEmail(key)
      .then(() => setStatus(VERIFY_STATUS.SUCCESSFUL))
      .catch(() => setStatus(VERIFY_STATUS.FAILURE));
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
              Go to login
            </button>
          </div>
        );
      case VERIFY_STATUS.FAILURE:
      default:
        return (
          <div className="flex flex-col items-center">
            <h2 className="text-2xl font-semibold mb-2">
              Invalid or expired link
            </h2>
            <p className="text-zinc-600 mb-4">
              Please request a new confirmation email.
            </p>
            <button
              className="border px-10 md:px-16 py-8 mb-4 hover:bg-sky-400 hover:text-white"
              onClick={() => resendVerify(uid)}
            >
              Go to login
            </button>
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
