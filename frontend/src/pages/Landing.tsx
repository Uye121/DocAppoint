import React from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import Spinner from "../components/Spinner";

const Landing = (): React.JSX.Element => {
  const { user, loading } = useAuth();
  console.log("user: ", user);

  if (loading) return <Spinner />;

  if (!user) return <Navigate to="/login" replace />;

  switch (user.userRole) {
    case "patient":
      return <Navigate to="/patient-home" replace />;
    case "provider":
      return <Navigate to="/provider-home" replace />;
    // case "admin_staff":
    //   return <Navigate to="/admin-dashboard" replace />;
    default:
      return <Navigate to="/onboard" replace />;
  }
};

export default Landing;
