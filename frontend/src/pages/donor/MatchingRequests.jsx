import { useEffect, useState, useCallback } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  Building2,
  MapPin,
  Clock,
  ShieldCheck,
  Check,
  X,
  RefreshCw,
  HeartHandshake,
} from "lucide-react";
import { api } from "../../services/api";
import { useNotification } from "../../context/NotificationContext";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { StatusBadge } from "../../components/common/StatusBadge";

export function MatchingRequests() {
  const { pathname } = useLocation();
  const { requestId: highlightedRequestId } = useParams();
  const isHistoryView = pathname.endsWith("/history");

  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState({});
  const [consentMap, setConsentMap] = useState({});
  const [selectedFilter, setSelectedFilter] = useState(null);
  const filterTab = selectedFilter ?? (isHistoryView ? "responded" : "all");

  const { notifySuccess, notifyError } = useNotification();

  const loadRequests = useCallback(async () => {
    try {
      const res = await api.get("/donors/matching-requests");
      if (res.success) {
        const items = res.data || [];
        setRequests(items);
        setConsentMap((prev) => {
          const next = { ...prev };
          items.forEach((r) => {
            if (next[r.request_id] === undefined) {
              next[r.request_id] = true;
            }
          });
          return next;
        });
      }
    } catch (err) {
      notifyError(err.message || "Failed to load matching requests.");
    } finally {
      setLoading(false);
    }
  }, [notifyError]);

  useEffect(() => {
    let active = true;
    async function init() {
      try {
        const res = await api.get("/donors/matching-requests");
        if (!active) return;
        if (res.success) {
          const items = res.data || [];
          setRequests(items);
          setConsentMap((prev) => {
            const next = { ...prev };
            items.forEach((r) => {
              if (next[r.request_id] === undefined) {
                next[r.request_id] = true;
              }
            });
            return next;
          });
        }
      } catch (err) {
        if (active) notifyError(err.message || "Failed to load matching requests.");
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
    loadRequests();
  };

  const handleConsentToggle = (requestId) => {
    setConsentMap((prev) => ({
      ...prev,
      [requestId]: !prev[requestId],
    }));
  };

  const handleRespond = async (requestId, status) => {
    const consent = consentMap[requestId] ?? true;
    setActionInProgress((prev) => ({ ...prev, [requestId]: true }));

    try {
      const res = await api.post(`/donors/requests/${requestId}/respond`, {
        status,
        consent_share_contact: consent,
      });

      if (res.success) {
        if (status === "accepted") {
          notifySuccess(
            consent
              ? "Request accepted. Your contact information was shared with the requester."
              : "Request accepted anonymously. Please coordinate directly at the hospital blood bank."
          );
        } else {
          notifySuccess(`Request marked as ${status}.`);
        }
        await loadRequests();
      }
    } catch (err) {
      notifyError(err.message || "Failed to record response.");
    } finally {
      setActionInProgress((prev) => ({ ...prev, [requestId]: false }));
    }
  };

  if (loading) {
    return <LoadingSpinner text="Retrieving proximity blood requests..." />;
  }

  const displayedRequests = requests.filter((r) => {
    if (highlightedRequestId && r.request_id !== highlightedRequestId) return false;
    if (filterTab === "pending") return r.response_status === "pending";
    if (filterTab === "responded") return r.response_status !== "pending";
    return true;
  });

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h3 className="fw-bold mb-1">
            {isHistoryView ? "Donor Response History" : "Matching Blood Requests"}
          </h3>
          <p className="text-muted small mb-0">
            Emergency requisitions matched by blood group and proximity within 10 km.
          </p>
        </div>
        <div className="d-flex flex-wrap gap-2">
          <div className="btn-group btn-group-sm">
            <button
              type="button"
              className={`btn ${filterTab === "all" ? "btn-danger" : "btn-outline-secondary"}`}
              onClick={() => setSelectedFilter("all")}
            >
              All ({requests.length})
            </button>
            <button
              type="button"
              className={`btn ${filterTab === "pending" ? "btn-danger" : "btn-outline-secondary"}`}
              onClick={() => setSelectedFilter("pending")}
            >
              Pending ({requests.filter((r) => r.response_status === "pending").length})
            </button>
            <button
              type="button"
              className={`btn ${filterTab === "responded" ? "btn-danger" : "btn-outline-secondary"}`}
              onClick={() => setSelectedFilter("responded")}
            >
              Responded ({requests.filter((r) => r.response_status !== "pending").length})
            </button>
          </div>

          <button
            type="button"
            onClick={handleRefresh}
            className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1"
          >
            <RefreshCw size={14} /> Refresh
          </button>

          <Link to="/donor/dashboard" className="btn btn-outline-secondary btn-sm">
            &larr; Dashboard
          </Link>
        </div>
      </div>

      {displayedRequests.length === 0 ? (
        <div className="card card-healthcare p-5 text-center">
          <HeartHandshake size={48} className="text-muted mx-auto mb-3" />
          <h5 className="fw-bold text-dark">No Matching Requests Found</h5>
          <p className="text-muted small mb-0">
            {filterTab === "pending"
              ? "You have no pending blood requests awaiting response."
              : "Requests appear here once a verified hospital or approved requester dispatches matching alerts."}
          </p>
        </div>
      ) : (
        <div className="row g-3">
          {displayedRequests.map((req) => {
            const isPending = req.response_status === "pending";
            const isAccepted = req.response_status === "accepted";
            const isDeclined = req.response_status === "declined";
            const isClosedRequest = ["fulfilled", "cancelled", "expired"].includes(req.request_status);
            const busy = actionInProgress[req.request_id];

            return (
              <div key={req.request_id} className="col-12">
                <div
                  className={`card card-healthcare p-4 ${
                    isAccepted ? "border-success" : isDeclined ? "border-muted" : "border-danger"
                  }`}
                >
                  <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-start gap-3">
                    <div>
                      <div className="d-flex flex-wrap align-items-center gap-2 mb-2">
                        <span className="badge bg-danger fs-6 px-2 py-1">{req.blood_group}</span>
                        <StatusBadge status={req.urgency} />
                        <span className="badge bg-light text-dark border">
                          {req.units_needed} Unit(s) Needed
                        </span>
                        <span className="badge bg-info text-dark">
                          ~{req.distance_km} km away
                        </span>
                        <StatusBadge status={req.request_status} />
                      </div>

                      <h5 className="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
                        <Building2 size={20} className="text-danger" />
                        {req.hospital_name}
                      </h5>

                      <div className="d-flex flex-wrap gap-3 text-muted small mt-2">
                        <span className="d-flex align-items-center gap-1">
                          <MapPin size={15} /> Locality: <strong>{req.locality}</strong>
                        </span>
                        <span className="d-flex align-items-center gap-1">
                          <Clock size={15} /> Required By: <strong>{req.required_by_date}</strong>
                        </span>
                      </div>
                    </div>

                    <div className="text-md-end">
                      <div className="small text-muted mb-1">Your Response Status:</div>
                      <StatusBadge status={req.response_status} />
                    </div>
                  </div>

                  {/* Action Bar for Pending Requests */}
                  {isPending && !isClosedRequest && (
                    <div className="mt-4 pt-3 border-top">
                      <div className="form-check form-switch mb-3">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id={`consent-${req.request_id}`}
                          checked={consentMap[req.request_id] ?? true}
                          onChange={() => handleConsentToggle(req.request_id)}
                        />
                        <label
                          className="form-check-label small fw-semibold"
                          htmlFor={`consent-${req.request_id}`}
                        >
                          Share my phone number and email with requester upon acceptance
                        </label>
                      </div>

                      <div className="d-flex flex-wrap gap-2">
                        <button
                          onClick={() => handleRespond(req.request_id, "accepted")}
                          disabled={busy}
                          className="btn btn-success btn-sm d-flex align-items-center gap-1 px-3"
                        >
                          <Check size={16} /> Accept Request
                        </button>
                        <button
                          onClick={() => handleRespond(req.request_id, "declined")}
                          disabled={busy}
                          className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1 px-3"
                        >
                          <X size={16} /> Decline
                        </button>
                        <button
                          onClick={() => handleRespond(req.request_id, "unavailable")}
                          disabled={busy}
                          className="btn btn-outline-secondary btn-sm px-3"
                        >
                          Mark Unavailable
                        </button>
                      </div>
                    </div>
                  )}

                  {isPending && isClosedRequest && (
                    <div className="mt-3 pt-2 border-top small text-muted">
                      This blood request is already <strong>{req.request_status}</strong> and no longer accepting responses.
                    </div>
                  )}

                  {!isPending && req.responded_at && (
                    <div className="mt-3 pt-2 border-top small text-muted d-flex align-items-center gap-2">
                      <ShieldCheck size={16} className="text-success" />
                      <span>
                        Responded on {new Date(req.responded_at).toLocaleString()} | Contact Sharing:{" "}
                        <strong>{req.contact_revealed ? "Granted" : "Withheld"}</strong>
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
