import { Outlet, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import Spinner from "./Spinner";

const ProtectedRoutes = () => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <Spinner />;

  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;

  // Prevent user from going to onboarding if already onboarded
  if (location.pathname === "/onboard" && user.userRole !== "unassigned") {
    if (user.userRole === "patient") {
      return <Navigate to="/patient-home" replace />;
    }
    if (user.userRole === "provider") {
      return <Navigate to="/provider-home" replace />;
    }
  }

  // Have to add the !== "onboard" part else it keep rendering and failing
  if (user.userRole === "unassigned" && location.pathname !== "/onboard") {
    return <Navigate to="/onboard" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoutes;
