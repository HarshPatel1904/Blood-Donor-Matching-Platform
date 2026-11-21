import { useAuth } from "../../context/AuthContext";
import { Link, useLocation } from "react-router-dom";
import { PlusCircle, ListFilter } from "lucide-react";
import { RequestManager } from "../../components/requests/RequestManager";

export function RequesterDashboard() {
  const { user } = useAuth();
  const { pathname } = useLocation();

  const section = pathname.endsWith("/create-request")
    ? "create"
    : pathname.endsWith("/my-requests")
    ? "list"
    : "overview";

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-0 text-dark">
            Welcome back, <span className="text-danger">{user?.full_name}</span>
          </h1>
        </div>
        <div className="d-flex gap-2">
          <Link to="/requester/create-request" className="btn btn-blood btn-sm d-flex align-items-center gap-1">
            <PlusCircle size={16} /> Request Blood
          </Link>
          <Link to="/requester/my-requests" className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1">
            <ListFilter size={16} /> My Requests
          </Link>
        </div>
      </div>

      <div className="alert alert-info small mb-4" role="alert">
        Individual requests require administrator approval before donor matching alerts are dispatched. Once approved, click <strong>Notify Donors</strong> on your request below.
      </div>

      <RequestManager mode="individual" section={section} />
    </div>
  );
}
