import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { SyncLoader } from "react-spinners";

import { VERIFY_STATUS, type VerifyStatus, type ResendVerifyPayload } from "../types/auth";
import { verifyEmail, resendVerify } from "../api/auth";

const VerifyEmail = (): React.JSX.Element => {
  const [searchParams] = useSearchParams();
  const nav = useNavigate();
  const [status, setStatus] = useState<VerifyStatus>(VERIFY_STATUS.LOADING);
  const [uid, setUid] = useState<ResendVerifyPayload | null>(null);

  useEffect(() => {
    const uid = searchParams.get('uid');
    const token = searchParams.get('token');

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

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-8 border rounded-xl shadow-lg text-center max-w-sm">
        {status === VERIFY_STATUS.LOADING && (
          <SyncLoader
            size={30}
            color="#94D928"
            loading={true}
          />
        )}
        {status === VERIFY_STATUS.SUCCESSFUL && (
          <>
            <h2 className="text-2xl font-semibold mb-2">Email confirmed!</h2>
            <button onClick={() => nav('/login')}>
              Go to login
            </button>
          </>
        )}
        {status === VERIFY_STATUS.FAILURE && uid && (
          <>
            <h2 className="text-2xl font-semibold mb-2">Invalid or expired link</h2>
            <p className="text-zinc-600 mb-4">Please request a new confirmation email.</p>
            <button onClick={() => resendVerify(uid)}>
              Go to login
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default VerifyEmail;
