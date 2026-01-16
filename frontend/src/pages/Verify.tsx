import React from "react";
import { useNavigate } from "react-router-dom";

const Verify = (): React.JSX.Element => {
  const nav = useNavigate();

  const handleRedirect = () => {
    nav("/login");
  };

  return (
    <div>
      <div className="text-center text-2xl pt-10 text-gray-500">
        Verify Email
      </div>
      <div className="text-center text-2base pt-8 text-gray-500">
        Please check email to verify email.
      </div>
      <div className="text-center">
        <button
          className="border border-black px-8 py-4 text-sm hover:bg-black hover:text-white transition-all duration-500"
          onClick={handleRedirect}
        >
          Back to login
        </button>
      </div>
    </div>
  );
};

export default Verify;
