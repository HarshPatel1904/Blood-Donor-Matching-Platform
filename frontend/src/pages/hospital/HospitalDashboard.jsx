import { useAuth } from "../../context/AuthContext";
import { Link, useLocation } from "react-router-dom";
import { PlusCircle, Activity } from "lucide-react";
import { StatusBadge } from "../../components/common/StatusBadge";
import { RequestManager } from "../../components/requests/RequestManager";

export function HospitalDashboard() {
  const { user } = useAuth();
  const { pathname } = useLocation();

  const hospitalProfile = user?.hospital_profile || user || {};
  const hospitalName = hospitalProfile.hospital_name || "Hospital Staff";
  const verificationStatus = hospitalProfile.verification_status || "pending";
  const defaultLocality = hospitalProfile.locality || "Navrangpura";

  const section = pathname.endsWith("/create-request")
    ? "create"
    : pathname.endsWith("/manage-requests")
    ? "list"
    : "overview";

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h3 className="fw-bold mb-1">Hospital Emergency Desk</h3>
          <p className="text-muted small mb-0">
            {hospitalName} | Status: <StatusBadge status={verificationStatus} />
          </p>
        </div>
        <div className="d-flex gap-2">
          <Link to="/hospital/create-request" className="btn btn-blood btn-sm d-flex align-items-center gap-1">
            <PlusCircle size={16} /> Post Blood Requisition
          </Link>
          <Link to="/hospital/manage-requests" className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1">
            <Activity size={16} /> Manage Requisitions
          </Link>
        </div>
      </div>

      {verificationStatus !== "verified" && (
        <div className="alert alert-warning small mb-4" role="alert">
          Your hospital account is currently <strong>{verificationStatus}</strong>. Requisitions you submit will be queued for admin review until an administrator verifies your hospital profile.
        </div>
      )}

      <RequestManager
        mode="hospital"
        section={section}
        hospitalName={hospitalName}
        defaultLocality={defaultLocality}
        hospitalVerified={verificationStatus === "verified"}
      />
    </div>
  );
}
