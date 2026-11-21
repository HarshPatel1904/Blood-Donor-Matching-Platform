import { useEffect, useState, useCallback } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../../services/api";
import { useNotification } from "../../context/NotificationContext";
import {
  ShieldAlert,
  Users,
  HeartPulse,
  CheckCircle2,
  XCircle,
  Send,
  RefreshCw,
  Clock,
  FileText,
} from "lucide-react";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { StatusBadge } from "../../components/common/StatusBadge";
import { DocumentPreviewModal } from "../../components/common/DocumentPreviewModal";

export function AdminDashboard() {
  const { pathname } = useLocation();
  const { notifySuccess, notifyError, notifyInfo } = useNotification();

  const activeSection = pathname.endsWith("/verify-hospitals")
    ? "hospitals"
    : pathname.endsWith("/verify-requests")
    ? "requests"
    : "overview";

  const [stats, setStats] = useState(null);
  const [hospitals, setHospitals] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [previewDoc, setPreviewDoc] = useState(null);

  const loadAdminData = useCallback(async () => {
    try {
      const [statsRes, hospRes, reqRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/hospitals"),
        api.get("/admin/requests"),
      ]);
      if (statsRes.success) setStats(statsRes.data);
      if (hospRes.success) setHospitals(hospRes.data || []);
      if (reqRes.success) setRequests(reqRes.data || []);
    } catch (err) {
      notifyError(err.message || "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }, [notifyError]);

  useEffect(() => {
    let active = true;
    async function init() {
      try {
        const [statsRes, hospRes, reqRes] = await Promise.all([
          api.get("/admin/stats"),
          api.get("/admin/hospitals"),
          api.get("/admin/requests"),
        ]);
        if (!active) return;
        if (statsRes.success) setStats(statsRes.data);
        if (hospRes.success) setHospitals(hospRes.data || []);
        if (reqRes.success) setRequests(reqRes.data || []);
      } catch (err) {
        if (active) notifyError(err.message || "Failed to load admin data.");
      } finally {
        if (active) setLoading(false);
      }
    }
    init();
    return () => {
      active = false;
    };
  }, [notifyError]);

  const handleRefresh = () => {
    setLoading(true);
    loadAdminData();
  };

  const handleVerifyHospital = async (hospitalId, status) => {
    setBusyId(hospitalId);
    try {
      const res = await api.patch(`/admin/hospitals/${hospitalId}/verify`, {
        status,
        notes: `Updated via Admin Portal (${status})`,
      });
      if (res.success) {
        notifySuccess(res.message || `Hospital marked as ${status}.`);
        await loadAdminData();
      }
    } catch (err) {
      notifyError(err.message || "Failed to update hospital verification.");
    } finally {
      setBusyId(null);
    }
  };

  const handleReviewRequest = async (requestId, status, alsoDispatch = false) => {
    setBusyId(requestId);
    try {
      const res = await api.patch(`/admin/requests/${requestId}/verify`, {
        status,
        notes: `Reviewed via Admin Portal (${status})`,
      });
      if (res.success) {
        notifySuccess(res.message || `Request ${status}.`);
        if (alsoDispatch && status === "approved") {
          try {
            const disp = await api.post(`/matching/${requestId}/dispatch`, { radius: 10 });
            if (disp.success) {
              notifySuccess(disp.message || "Matching donors notified.");
            }
          } catch (dispErr) {
            notifyInfo(`Request approved, but dispatch note: ${dispErr.message}`);
          }
        }
        await loadAdminData();
      }
    } catch (err) {
      notifyError(err.message || "Failed to review blood request.");
    } finally {
      setBusyId(null);
    }
  };

  const handleDispatch = async (requestId) => {
    setBusyId(requestId);
    try {
      const res = await api.post(`/matching/${requestId}/dispatch`, { radius: 10 });
      if (res.success) {
        notifySuccess(res.message || "Matching donors notified.");
        await loadAdminData();
      }
    } catch (err) {
      notifyError(err.message || "Failed to dispatch notifications.");
    } finally {
      setBusyId(null);
    }
  };

  if (loading) return <LoadingSpinner text="Aggregating platform metrics..." />;

  const showHospitals = activeSection === "overview" || activeSection === "hospitals";
  const showRequests = activeSection === "overview" || activeSection === "requests";

  return (
    <div className="d-flex flex-column gap-4">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
        <div>
          <h3 className="fw-bold mb-1">Administrator Control Overview</h3>
          <p className="text-muted small mb-0">
            Verify hospitals, approve individual blood requests, and dispatch matching alerts.
          </p>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats Row */}
      <div className="row g-3">
        <div className="col-6 col-md-3">
          <div className="card card-healthcare p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <div className="text-muted small">Registered Donors</div>
                <h3 className="fw-bold text-danger mb-0">{stats?.users?.donors || 0}</h3>
              </div>
              <Users size={28} className="text-danger opacity-75" />
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="card card-healthcare p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <div className="text-muted small">Pending Requests</div>
                <h3 className="fw-bold text-warning mb-0">{stats?.requests?.pending_verification || 0}</h3>
              </div>
              <ShieldAlert size={28} className="text-warning opacity-75" />
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="card card-healthcare p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <div className="text-muted small">Verified Hospitals</div>
                <h3 className="fw-bold text-success mb-0">{stats?.users?.hospitals_verified || 0}</h3>
              </div>
              <CheckCircle2 size={28} className="text-success opacity-75" />
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="card card-healthcare p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <div className="text-muted small">Open Requisitions</div>
                <h3 className="fw-bold text-primary mb-0">{stats?.requests?.open || 0}</h3>
              </div>
              <HeartPulse size={28} className="text-primary opacity-75" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Navigation Pills */}
      <div className="d-flex flex-wrap gap-2">
        <Link
          to="/admin/dashboard"
          className={`btn btn-sm ${activeSection === "overview" ? "btn-danger" : "btn-outline-secondary"}`}
        >
          Overview
        </Link>
        <Link
          to="/admin/verify-hospitals"
          className={`btn btn-sm ${activeSection === "hospitals" ? "btn-danger" : "btn-outline-secondary"}`}
        >
          Verify Hospitals ({hospitals.filter((h) => h.verification_status === "pending").length} pending)
        </Link>
        <Link
          to="/admin/verify-requests"
          className={`btn btn-sm ${activeSection === "requests" ? "btn-danger" : "btn-outline-secondary"}`}
        >
          Review Requests ({requests.filter((r) => r.verification_status === "pending").length} pending)
        </Link>
      </div>

      {/* Review Blood Requests */}
      {showRequests && (
        <div className="card card-healthcare p-4">
          <h5 className="fw-bold mb-3">Blood Requests Verification & Dispatch</h5>
          {requests.length === 0 ? (
            <div className="text-muted small">No blood requests found.</div>
          ) : (
            <div className="d-flex flex-column gap-3">
              {requests.map((req) => {
                const isBusy = busyId === req.request_id;
                const isClosed = ["fulfilled", "cancelled", "expired"].includes(req.request_status);
                return (
                  <div key={req.request_id} className="border rounded p-3 bg-white">
                    <div className="d-flex flex-column flex-lg-row justify-content-between gap-2">
                      <div>
                        <div className="d-flex flex-wrap align-items-center gap-2 mb-1">
                          <span className="badge bg-danger">{req.blood_group}</span>
                          <span className="badge bg-light text-dark border text-uppercase">
                            {req.request_type}
                          </span>
                          <StatusBadge status={req.urgency} />
                          <StatusBadge status={req.verification_status} />
                          <StatusBadge status={req.request_status} />
                        </div>
                        <div className="fw-bold">{req.hospital_name}</div>
                        <div className="small text-muted">
                          Requester: {req.requester_name} | Locality: {req.locality} | Units: {req.units_needed} | Required By: {req.required_by_date}
                        </div>
                        <div className="mt-2 d-flex align-items-center gap-2">
                          {req.requisition_doc_url ? (
                            <button
                              type="button"
                              onClick={() =>
                                setPreviewDoc({
                                  path: req.requisition_doc_url,
                                  title: `Requisition Document — ${req.hospital_name} (${req.blood_group})`,
                                })
                              }
                              className="btn btn-outline-dark btn-sm d-flex align-items-center gap-1"
                            >
                              <FileText size={14} /> View Uploaded Document
                            </button>
                          ) : (
                            <span className="badge bg-light text-muted border small">
                              No requisition document uploaded
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="d-flex flex-wrap align-items-center gap-2">
                        {req.verification_status !== "approved" && (
                          <>
                            <button
                              type="button"
                              disabled={isBusy}
                              onClick={() => handleReviewRequest(req.request_id, "approved", true)}
                              className="btn btn-success btn-sm d-flex align-items-center gap-1"
                            >
                              <CheckCircle2 size={14} /> Approve & Notify Donors
                            </button>
                            <button
                              type="button"
                              disabled={isBusy}
                              onClick={() => handleReviewRequest(req.request_id, "approved", false)}
                              className="btn btn-outline-success btn-sm"
                            >
                              Approve Only
                            </button>
                          </>
                        )}

                        {req.verification_status === "approved" && !isClosed && (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => handleDispatch(req.request_id)}
                            className="btn btn-blood btn-sm d-flex align-items-center gap-1"
                          >
                            <Send size={14} /> Notify Donors
                          </button>
                        )}

                        {req.verification_status === "pending" && (
                          <>
                            <button
                              type="button"
                              disabled={isBusy}
                              onClick={() => handleReviewRequest(req.request_id, "on_hold")}
                              className="btn btn-outline-warning btn-sm d-flex align-items-center gap-1"
                            >
                              <Clock size={14} /> Hold
                            </button>
                            <button
                              type="button"
                              disabled={isBusy}
                              onClick={() => handleReviewRequest(req.request_id, "rejected")}
                              className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1"
                            >
                              <XCircle size={14} /> Reject
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Hospital Verification */}
      {showHospitals && (
        <div className="card card-healthcare p-4">
          <h5 className="fw-bold mb-3">Registered Hospitals</h5>
          {hospitals.length === 0 ? (
            <div className="text-muted small">No registered hospitals found.</div>
          ) : (
            <div className="d-flex flex-column gap-3">
              {hospitals.map((h) => {
                const isBusy = busyId === h.hospital_id;
                return (
                  <div key={h.hospital_id} className="border rounded p-3 bg-white">
                    <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2">
                      <div>
                        <div className="d-flex align-items-center gap-2 mb-1">
                          <strong>{h.hospital_name}</strong>
                          <StatusBadge status={h.verification_status} />
                        </div>
                        <div className="small text-muted">
                          License: {h.license_number} | Locality: {h.locality} | Phone: {h.official_phone}
                        </div>
                      </div>
                      <div className="d-flex gap-2">
                        {h.verification_status !== "verified" && (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => handleVerifyHospital(h.hospital_id, "verified")}
                            className="btn btn-success btn-sm d-flex align-items-center gap-1"
                          >
                            <CheckCircle2 size={14} /> Verify
                          </button>
                        )}
                        {h.verification_status !== "rejected" && (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => handleVerifyHospital(h.hospital_id, "rejected")}
                            className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1"
                          >
                            <XCircle size={14} /> Reject
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {previewDoc && (
        <DocumentPreviewModal
          docPath={previewDoc.path}
          title={previewDoc.title}
          onClose={() => setPreviewDoc(null)}
        />
      )}
    </div>
  );
}
