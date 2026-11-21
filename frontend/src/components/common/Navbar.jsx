import { Link, useNavigate } from "react-router-dom";
import { HeartPulse, User, LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { getPortalConfig } from "../../utils/portalConfig";

export function Navbar() {
  const { user, isAuthenticated, role, logout } = useAuth();
  const navigate = useNavigate();
  const portal = getPortalConfig();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const getDashboardPath = () => {
    switch (role) {
      case "donor":
        return "/donor/dashboard";
      case "requester":
        return "/requester/dashboard";
      case "hospital":
        return "/hospital/dashboard";
      case "admin":
        return "/admin/dashboard";
      default:
        return "/";
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm border-bottom border-danger border-2">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center gap-2 fw-bold text-white" to="/">
          <HeartPulse size={26} className="text-danger" />
          <span>RaktSetu</span>
        </Link>

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navContent"
          aria-controls="navContent"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navContent">
          <div className="d-flex align-items-center gap-3 ms-auto">
            {isAuthenticated ? (
              <div className="d-flex align-items-center gap-2">
                <Link to={getDashboardPath()} className="btn btn-outline-light btn-sm d-flex align-items-center gap-1">
                  <User size={16} />
                  <span>{user?.full_name || "Dashboard"}</span>
                  <span className="badge bg-danger text-uppercase ms-1" style={{ fontSize: "0.65rem" }}>
                    {role}
                  </span>
                </Link>
                {!portal.isDirectAdmin && (
                  <button onClick={handleLogout} className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1" title="Sign out">
                    <LogOut size={16} />
                    <span className="d-none d-md-inline">Logout</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="d-flex align-items-center gap-2">
                <Link to="/login" className="btn btn-outline-light btn-sm px-3">
                  Sign In
                </Link>
                <Link to="/register" className="btn btn-blood btn-sm px-3">
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}