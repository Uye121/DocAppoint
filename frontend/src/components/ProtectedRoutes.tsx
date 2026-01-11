import { Outlet, Navigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import Spinner from "../components/Spinner";

const ProtectedRoutes = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <Spinner />;
  }
  
  return user ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoutes;
