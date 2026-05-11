import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { UserRole } from "../api/types";
import { useAuth } from "./AuthProvider";
import { LoadingState } from "../components/LoadingState";

export function ProtectedRoute({ roles }: { roles?: UserRole[] }) {
  const { isAuthenticated, loading, hasRole } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingState label="Проверяем авторизацию" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!hasRole(roles)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
