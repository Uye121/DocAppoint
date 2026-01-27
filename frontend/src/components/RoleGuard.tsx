import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import Spinner from "./Spinner";

type Props = {
  allowed: ("patient" | "provider")[];
  children: React.ReactNode;
};

const RoleGuard = ({ allowed, children }: Props) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;

  const userRole = user.userRole;
  if (userRole === "unassigned" || !allowed.includes(userRole)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

export default RoleGuard;
