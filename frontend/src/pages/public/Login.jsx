import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Lock, Mail, HeartPulse, UserPlus, UserCheck, Building2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useNotification } from "../../context/NotificationContext";
import { BloodDropTransition } from "../../components/common/BloodDropTransition";
import { getPortalConfig } from "../../utils/portalConfig";

const SIGN_IN_ROLES = [
  {
    value: "donor",
    label: "Donor",
    title: "Voluntary Donor",
    icon: UserPlus,
  },
  {
    value: "requester",
    label: "Requester",
    title: "Individual Requester",
    icon: UserCheck,
  },
  {
    value: "hospital",
    label: "Hospital Staff",
    title: "Hospital Staff",
    icon: Building2,
  },
];

export function Login() {
  const portal = getPortalConfig();
  const initialRole = SIGN_IN_ROLES.some((r) => r.value === portal.role) ? portal.role : "donor";
  const [selectedRole, setSelectedRole] = useState(initialRole);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Transition state
  const [showTransition, setShowTransition] = useState(false);
  const [redirectPath, setRedirectPath] = useState("/");

  const { login } = useAuth();
  const { notifyError } = useNotification();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || null;
  const activeRoleMeta = SIGN_IN_ROLES.find((r) => r.value === selectedRole) || SIGN_IN_ROLES[0];

  const getTargetPortal = (userRole) => {
    if (from && from.startsWith(`/${userRole}`)) return from;
    switch (userRole) {
      case "donor":
        return "/donor/dashboard";
      case "requester":
        return "/requester/dashboard";
      case "hospital":
        return "/hospital/dashboard";
      default:
        return "/";
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      notifyError("Please enter both email and password.");
      return;
    }

    setSubmitting(true);
    try {
      const user = await login(email, password, selectedRole);
      const target = getTargetPortal(user.role);

      setRedirectPath(target);
      setShowTransition(true);
    } catch (err) {
      notifyError(err.message || "Invalid credentials.");
      setSubmitting(false);
    }
  };

  const handleProceed = () => {
    setShowTransition(false);
    navigate(redirectPath, { replace: true });
  };

  return (
    <div className="container py-5">
      {/* 5.5s Pure Centered Liquid Blood Drop Transition */}
      <BloodDropTransition
        isOpen={showTransition}
        onProceed={handleProceed}
        duration={5500}
      />

      <div className="row justify-content-center">
        <div className="col-md-8 col-lg-6">
          <div className="card card-healthcare p-4 p-md-5">
            <div className="text-center mb-4">
              <HeartPulse size={38} className="text-danger mb-2" />
              <h3 className="fw-bold">Sign In to RaktSetu</h3>
              <p className="text-muted small mb-0">
                Select what you want to sign in for ({portal.label})
              </p>
            </div>

            <div className="mb-4">
              <label className="form-label small fw-semibold text-muted d-block mb-2">
                What do you want to sign in for?
              </label>
              <div className="row g-2">
                {SIGN_IN_ROLES.map((item) => {
                  const Icon = item.icon;
                  const active = selectedRole === item.value;
                  return (
                    <div key={item.value} className="col-4">
                      <button
                        type="button"
                        onClick={() => setSelectedRole(item.value)}
                        className={`btn w-100 py-2 px-2 d-flex flex-column align-items-center gap-1 small fw-semibold ${
                          active ? "btn-danger text-white" : "btn-outline-secondary"
                        }`}
                      >
                        <Icon size={18} />
                        <span>{item.label}</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label small fw-semibold">Email Address</label>
                <div className="input-group">
                  <span className="input-group-text bg-white"><Mail size={16} /></span>
                  <input
                    type="email"
                    className="form-control"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="form-label small fw-semibold">Password</label>
                <div className="input-group">
                  <span className="input-group-text bg-white"><Lock size={16} /></span>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-blood w-100 py-2 fw-semibold" disabled={submitting}>
                {submitting ? "Signing In..." : `Sign In as ${activeRoleMeta.title}`}
              </button>
            </form>

            <div className="mt-4 pt-3 border-top text-center small text-muted">
              Don't have an account? <Link to="/register" className="text-danger fw-semibold">Create one here</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
