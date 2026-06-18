import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import ProtectedRoute, { PermissionRoute } from "./components/ProtectedRoute.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";

import Login from "./pages/Login.jsx";

const Dashboard = lazy(() => import("./pages/Dashboard.jsx"));
const Students = lazy(() => import("./pages/Students.jsx"));
const Teachers = lazy(() => import("./pages/Teachers.jsx"));
const Groups = lazy(() => import("./pages/Groups.jsx"));
const Attendance = lazy(() => import("./pages/Attendance.jsx"));
const Payments = lazy(() => import("./pages/Payments.jsx"));
const Lms = lazy(() => import("./pages/Lms.jsx"));
const Parent = lazy(() => import("./pages/Parent.jsx"));
const Settings = lazy(() => import("./pages/Settings.jsx"));

function PageFallback() {
  return <div className="p-2 text-sm text-slate-400">Loading...</div>;
}

function Guarded({ children, permissions = [], roles = [] }) {
  return (
    <PermissionRoute permissions={permissions} roles={roles}>
      <Suspense fallback={<PageFallback />}>{children}</Suspense>
    </PermissionRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Guarded permissions={["analytics:read"]}><Dashboard /></Guarded>} />
        <Route path="/students" element={<Guarded permissions={["student:read"]}><Students /></Guarded>} />
        <Route path="/teachers" element={<Guarded permissions={["teacher:read"]}><Teachers /></Guarded>} />
        <Route path="/groups" element={<Guarded permissions={["group:read"]}><Groups /></Guarded>} />
        <Route path="/attendance" element={<Guarded permissions={["attendance:read"]}><Attendance /></Guarded>} />
        <Route path="/payments" element={<Guarded permissions={["payment:read"]}><Payments /></Guarded>} />
        <Route path="/lms" element={<Guarded roles={["admin", "manager", "teacher", "student"]}><Lms /></Guarded>} />
        <Route path="/parent" element={<Guarded roles={["parent"]}><Parent /></Guarded>} />
        <Route path="/settings" element={<Suspense fallback={<PageFallback />}><Settings /></Suspense>} />
      </Route>
    </Routes>
  );
}
