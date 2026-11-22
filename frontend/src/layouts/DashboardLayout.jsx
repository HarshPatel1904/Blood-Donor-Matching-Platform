import { Outlet, NavLink } from "react-router-dom";
import { Navbar } from "../components/common/Navbar";
import { useAuth } from "../context/AuthContext";
import { getPortalConfig } from "../utils/portalConfig";
import {
  LayoutDashboard,
  HeartHandshake,
  Clock,
  UserCheck,
  PlusCircle,
  ListFilter,
  ShieldCheck,
  Activity,
} from "lucide-react";

export function DashboardLayout() {
  const { role } = useAuth();
  const portal = getPortalConfig();

  const renderNavLinks = () => {
    switch (role) {
      case "donor":
        return (
          <>
            <NavLink to="/donor/dashboard" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <LayoutDashboard size={18} /> Dashboard
            </NavLink>
            <NavLink to="/donor/matching-requests" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <HeartHandshake size={18} /> Matching Requests
            </NavLink>
            <NavLink to="/donor/history" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <Clock size={18} /> Response History
            </NavLink>
          </>
        );
      case "requester":
        return (
          <>
            <NavLink to="/requester/dashboard" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <LayoutDashboard size={18} /> Dashboard
            </NavLink>
            <NavLink to="/requester/create-request" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <PlusCircle size={18} /> Request Blood
            </NavLink>
            <NavLink to="/requester/my-requests" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <ListFilter size={18} /> Track Requests
            </NavLink>
          </>
        );
      case "hospital":
        return (
          <>
            <NavLink to="/hospital/dashboard" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <LayoutDashboard size={18} /> Dashboard
            </NavLink>
            <NavLink to="/hospital/create-request" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <PlusCircle size={18} /> Post Requisition
            </NavLink>
            <NavLink to="/hospital/manage-requests" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <Activity size={18} /> Manage Requisitions
            </NavLink>
          </>
        );
      case "admin":
        return (
          <>
            <NavLink to="/admin/dashboard" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <LayoutDashboard size={18} /> Platform Overview
            </NavLink>
            <NavLink to="/admin/verify-hospitals" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <ShieldCheck size={18} /> Verify Hospitals
            </NavLink>
            <NavLink to="/admin/verify-requests" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              <UserCheck size={18} /> Review Requests
            </NavLink>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <>
      <Navbar />
      <div className="container-fluid flex-grow-1">
        <div className="row">
          <aside className="col-12 col-md-3 col-lg-2 p-3 dashboard-sidebar">
            <div className="text-uppercase small fw-bold text-muted mb-2 px-2">Navigation</div>
            <nav className="nav flex-row flex-md-column flex-wrap gap-1">{renderNavLinks()}</nav>
            {(portal.isDirectAdmin || role === "admin") && (
              <div className="mt-3 px-2">
                <span className="badge bg-light text-secondary border fw-normal">
                  v1.1 &bull; CI/CD Live
                </span>
              </div>
            )}
          </aside>
          <main className="col-12 col-md-9 col-lg-10 p-4">
            <Outlet />
          </main>
        </div>
      </div>
      {!portal.isDirectAdmin && (
        <footer className="py-2 text-center border-top bg-white">
          <span className="text-muted small">v1.1 &bull; Auto-Deployed via CI/CD</span>
        </footer>
      )}
    </>
  );
}