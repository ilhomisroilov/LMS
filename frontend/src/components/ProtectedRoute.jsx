import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { canAccess, defaultPathForUser } from "../utils/authz.js";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export function PermissionRoute({ children, permissions = [], roles = [] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!canAccess(user, { permissions, roles })) {
    return <Navigate to={defaultPathForUser(user)} replace />;
  }
  return children;
}
