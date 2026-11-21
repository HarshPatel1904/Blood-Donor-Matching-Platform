import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { getPortalConfig } from "./utils/portalConfig";
import { MainLayout } from "./layouts/MainLayout";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { ProtectedRoute } from "./components/common/ProtectedRoute";

// Public Pages
import { Home } from "./pages/public/Home";
import { Login } from "./pages/public/Login";
import { Register } from "./pages/public/Register";
import { Unauthorized } from "./pages/public/Unauthorized";

// Role Dashboards & Pages
import { DonorDashboard } from "./pages/donor/DonorDashboard";
import { MatchingRequests } from "./pages/donor/MatchingRequests";
import { RequesterDashboard } from "./pages/requester/RequesterDashboard";
import { HospitalDashboard } from "./pages/hospital/HospitalDashboard";
import { AdminDashboard } from "./pages/admin/AdminDashboard";

export default function App() {
  const portal = getPortalConfig();

  useEffect(() => {
    document.title = portal.tabTitle;
  }, [portal.tabTitle]);

  return (
    <Routes>
      {/* Public Pages wrapped in MainLayout */}
      <Route element={<MainLayout />}>
        <Route
          path="/"
          element={portal.isDirectAdmin ? <Navigate to="/admin/dashboard" replace /> : <Home />}
        />
        <Route path="/about" element={<Home />} />
        <Route path="/how-it-works" element={<Home />} />
        <Route
          path="/login"
          element={portal.isDirectAdmin ? <Navigate to="/admin/dashboard" replace /> : <Login />}
        />
        <Route
          path="/register"
          element={portal.isDirectAdmin ? <Navigate to="/admin/dashboard" replace /> : <Register />}
        />
        <Route path="/unauthorized" element={<Unauthorized />} />
      </Route>

      {/* Donor Protected Routes */}
      <Route
        path="/donor"
        element={
          <ProtectedRoute allowedRoles={["donor"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<DonorDashboard />} />
        <Route path="matching-requests" element={<MatchingRequests />} />
        <Route path="requests/:requestId" element={<MatchingRequests />} />
        <Route path="history" element={<MatchingRequests />} />
      </Route>

      {/* Individual Requester Protected Routes */}
      <Route
        path="/requester"
        element={
          <ProtectedRoute allowedRoles={["requester"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<RequesterDashboard />} />
        <Route path="create-request" element={<RequesterDashboard />} />
        <Route path="my-requests" element={<RequesterDashboard />} />
      </Route>

      {/* Hospital Protected Routes */}
      <Route
        path="/hospital"
        element={
          <ProtectedRoute allowedRoles={["hospital"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<HospitalDashboard />} />
        <Route path="create-request" element={<HospitalDashboard />} />
        <Route path="manage-requests" element={<HospitalDashboard />} />
      </Route>

      {/* Admin Protected Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={["admin"]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="verify-hospitals" element={<AdminDashboard />} />
        <Route path="verify-requests" element={<AdminDashboard />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}