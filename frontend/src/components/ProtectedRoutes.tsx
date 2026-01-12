import { Outlet, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import Spinner from "./Spinner";

const ProtectedRoutes = () => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <Spinner />;

  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;

  if (location.pathname === '/onboard') return <Outlet />;

  if (user.userRole === "unassigned") {
    return <Navigate to="/onboard" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoutes;