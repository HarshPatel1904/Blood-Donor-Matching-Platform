import { useState, useEffect, useCallback } from "react";
import {
  PlusCircle,
  Send,
  Users,
  Eye,
  CheckCircle2,
  XCircle,
  RefreshCw,
  MapPin,
  Phone,
  Mail,
  Clock,
  ShieldCheck,
  FileText,
} from "lucide-react";
import { api } from "../../services/api";
import { useNotification } from "../../context/NotificationContext";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { StatusBadge } from "../common/StatusBadge";
import { DocumentPreviewModal } from "../common/DocumentPreviewModal";
import {
  BLOOD_GROUPS,
  DEFAULT_LOCALITIES,
  URGENCY_LEVELS,
  getDefaultRequiredDate,
} from "../../utils/constants";

/**
 * Shared blood request creation & lifecycle manager for Individual Requesters and Hospital Staff.
 */
export function RequestManager({
  mode = "individual",
  section = "overview",
  hospitalName = "",
  defaultLocality = "Navrangpura",
  hospitalVerified = false,
}) {
  const isHospital = mode === "hospital";
  const { notifySuccess, notifyError, notifyInfo } = useNotification();

  const [localities, setLocalities] = useState(DEFAULT_LOCALITIES);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [radiusKm, setRadiusKm] = useState(10);

  // Per-request interactive drawers & busy flags
  const [busyMap, setBusyMap] = useState({});
  const [previewMap, setPreviewMap] = useState({});
  const [responsesMap, setResponsesMap] = useState({});
  const [openDrawer, setOpenDrawer] = useState({});
  const [previewDoc, setPreviewDoc] = useState(null);

  const [formData, setFormData] = useState({
    blood_group: "B+",
    units_needed: 1,
    hospital_name: hospitalName || "",
    locality: defaultLocality || "Navrangpura",
    urgency: isHospital ? "urgent" : "normal",
    required_by_date: getDefaultRequiredDate(),
    auto_dispatch: isHospital && hospitalVerified,
    document: null,
  });

  const loadData = useCallback(async () => {
    try {
      const [reqRes, locRes] = await Promise.all([
        api.get("/requests/my"),
        api.get("/localities").catch(() => null),
      ]);
      if (reqRes?.success) {
        setRequests(reqRes.data || []);
      }
      if (locRes?.success && Array.isArray(locRes.data) && locRes.data.length > 0) {
        setLocalities(locRes.data.map((l) => l.name));
      }
    } catch (err) {
      notifyError(err.message || "Failed to load blood requests.");
    } finally {
      setLoading(false);
    }
  }, [notifyError]);

  useEffect(() => {
    let active = true;
    async function init() {
      try {
        const [reqRes, locRes] = await Promise.all([
          api.get("/requests/my"),
          api.get("/localities").catch(() => null),
        ]);
        if (!active) return;
        if (reqRes?.success) {
          setRequests(reqRes.data || []);
        }
        if (locRes?.success && Array.isArray(locRes.data) && locRes.data.length > 0) {
          setLocalities(locRes.data.map((l) => l.name));
        }
      } catch (err) {
        if (active) notifyError(err.message || "Failed to load blood requests.");
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
    loadData();
  };

  const handleFieldChange = (e) => {
    const { name, value, type, checked, files } = e.target;
    if (type === "file") {
      setFormData((prev) => ({ ...prev, document: files?.[0] || null }));
    } else if (type === "checkbox") {
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const endpoint = isHospital ? "/requests/hospital" : "/requests/individual";
      let payload;

      if (formData.document) {
        const fd = new FormData();
        fd.append("blood_group", formData.blood_group);
        fd.append("units_needed", String(formData.units_needed));
        if (!isHospital) {
          fd.append("hospital_name", formData.hospital_name);
        }
        fd.append("locality", formData.locality);
        fd.append("urgency", formData.urgency);
        fd.append("required_by_date", formData.required_by_date);
        fd.append("requisition_doc", formData.document);
        payload = fd;
      } else {
        payload = {
          blood_group: formData.blood_group,
          units_needed: Number(formData.units_needed),
          locality: formData.locality,
          urgency: formData.urgency,
          required_by_date: formData.required_by_date,
          ...(isHospital ? {} : { hospital_name: formData.hospital_name }),
        };
      }

      const res = await api.post(endpoint, payload);
      if (res.success && res.data) {
        notifySuccess(res.message || "Blood request submitted.");
        const created = res.data;

        if (formData.auto_dispatch && created.verification_status === "approved") {
          try {
            const dispatchRes = await api.post(`/matching/${created.request_id}/dispatch`, {
              radius: radiusKm,
            });
            if (dispatchRes.success) {
              notifySuccess(dispatchRes.message || "Matching donors notified.");
            }
          } catch (dispatchErr) {
            notifyInfo(`Request saved, but donor dispatch note: ${dispatchErr.message}`);
          }
        }

        setFormData((prev) => ({
          ...prev,
          units_needed: 1,
          hospital_name: isHospital ? prev.hospital_name : "",
          document: null,
        }));
        await loadData();
      }
    } catch (err) {
      notifyError(err.message || "Failed to submit blood request.");
    } finally {
      setSubmitting(false);
    }
  };

  const setRequestBusy = (requestId, flag) => {
    setBusyMap((prev) => ({ ...prev, [requestId]: flag }));
  };

  const handlePreviewMatches = async (requestId) => {
    setRequestBusy(requestId, true);
    try {
      const res = await api.get(`/matching/${requestId}/preview?radius=${radiusKm}`);
      if (res.success) {
        setPreviewMap((prev) => ({ ...prev, [requestId]: res.data }));
        setOpenDrawer((prev) => ({ ...prev, [requestId]: "preview" }));
      }
    } catch (err) {
      notifyError(err.message || "Failed to preview matching donors.");
    } finally {
      setRequestBusy(requestId, false);
    }
  };

  const handleDispatchDonors = async (requestId) => {
    setRequestBusy(requestId, true);
    try {
      const res = await api.post(`/matching/${requestId}/dispatch`, { radius: radiusKm });
      if (res.success) {
        notifySuccess(res.message || "Notifications sent to matching donors.");
        await loadData();
        await handleViewResponses(requestId);
      }
    } catch (err) {
      notifyError(err.message || "Failed to notify donors.");
    } finally {
      setRequestBusy(requestId, false);
    }
  };

  const handleViewResponses = async (requestId) => {
    setRequestBusy(requestId, true);
    try {
      const res = await api.get(`/requests/${requestId}/responses`);
      if (res.success) {
        setResponsesMap((prev) => ({ ...prev, [requestId]: res.data || [] }));
        setOpenDrawer((prev) => ({ ...prev, [requestId]: "responses" }));
      }
    } catch (err) {
      notifyError(err.message || "Failed to load donor responses.");
    } finally {
      setRequestBusy(requestId, false);
    }
  };

  const handleLifecycleChange = async (requestId, nextStatus) => {
    setRequestBusy(requestId, true);
    try {
      const res = await api.patch(`/requests/${requestId}/status`, {
        request_status: nextStatus,
      });
      if (res.success) {
        notifySuccess(res.message || `Request marked as ${nextStatus}.`);
        await loadData();
      }
    } catch (err) {
      notifyError(err.message || "Failed to update request status.");
    } finally {
      setRequestBusy(requestId, false);
    }
  };

  const showForm = section === "overview" || section === "create";
  const showList = section === "overview" || section === "list";

  const filteredRequests = requests.filter((req) =>
    statusFilter === "all" ? true : req.request_status === statusFilter
  );

  return (
    <div className="d-flex flex-column gap-4">
      {showForm && (
        <div className="card card-healthcare p-4">
          <div className="d-flex align-items-center gap-2 mb-3">
            <PlusCircle size={20} className="text-danger" />
            <h5 className="fw-bold mb-0">
              {isHospital ? "Post Hospital Blood Requisition" : "Submit Individual Blood Request"}
            </h5>
          </div>

          <form onSubmit={handleCreateSubmit}>
            <div className="row g-3">
              <div className="col-md-4">
                <label className="form-label small fw-semibold">Blood Group</label>
                <select
                  name="blood_group"
                  className="form-select"
                  value={formData.blood_group}
                  onChange={handleFieldChange}
                >
                  {BLOOD_GROUPS.map((bg) => (
                    <option key={bg} value={bg}>
                      {bg}
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-md-4">
                <label className="form-label small fw-semibold">Units Needed</label>
                <input
                  type="number"
                  name="units_needed"
                  min={1}
                  max={20}
                  className="form-control"
                  value={formData.units_needed}
                  onChange={handleFieldChange}
                  required
                />
              </div>

              <div className="col-md-4">
                <label className="form-label small fw-semibold">Urgency Level</label>
                <select
                  name="urgency"
                  className="form-select"
                  value={formData.urgency}
                  onChange={handleFieldChange}
                >
                  {URGENCY_LEVELS.map((u) => (
                    <option key={u.value} value={u.value}>
                      {u.label}
                    </option>
                  ))}
                </select>
              </div>

              {!isHospital && (
                <div className="col-md-6">
                  <label className="form-label small fw-semibold">Admitted Hospital Name</label>
                  <input
                    type="text"
                    name="hospital_name"
                    className="form-control"
                    placeholder="e.g., Civil Hospital Ahmedabad"
                    value={formData.hospital_name}
                    onChange={handleFieldChange}
                    required
                  />
                </div>
              )}

              <div className={isHospital ? "col-md-4" : "col-md-3"}>
                <label className="form-label small fw-semibold">Locality (Ahmedabad)</label>
                <select
                  name="locality"
                  className="form-select"
                  value={formData.locality}
                  onChange={handleFieldChange}
                >
                  {localities.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>

              <div className={isHospital ? "col-md-4" : "col-md-3"}>
                <label className="form-label small fw-semibold">Required By Date</label>
                <input
                  type="date"
                  name="required_by_date"
                  className="form-control"
                  value={formData.required_by_date}
                  onChange={handleFieldChange}
                  required
                />
              </div>

              <div className={isHospital ? "col-md-4" : "col-12"}>
                <label className="form-label small fw-semibold">
                  Requisition Document <span className="text-muted fw-normal">(optional PDF/PNG/JPG)</span>
                </label>
                <input
                  type="file"
                  name="document"
                  accept=".pdf,.png,.jpg,.jpeg"
                  className="form-control"
                  onChange={handleFieldChange}
                />
              </div>

              {isHospital && hospitalVerified && (
                <div className="col-12">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="autoDispatchCheck"
                      name="auto_dispatch"
                      checked={formData.auto_dispatch}
                      onChange={handleFieldChange}
                    />
                    <label className="form-check-label small fw-semibold" htmlFor="autoDispatchCheck">
                      Automatically notify matching donors within {radiusKm} km upon posting
                    </label>
                  </div>
                </div>
              )}

              <div className="col-12">
                <button type="submit" className="btn btn-blood px-4 fw-semibold" disabled={submitting}>
                  {submitting
                    ? "Submitting..."
                    : isHospital
                    ? "Post Blood Requisition"
                    : "Submit Blood Request"}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {showList && (
        <div className="card card-healthcare p-4">
          <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
            <div>
              <h5 className="fw-bold mb-0">
                {isHospital ? "Hospital Blood Requisitions" : "My Blood Requests"} ({filteredRequests.length})
              </h5>
              <div className="small text-muted">
                Preview eligible donors, dispatch alerts, and check consenting donor responses.
              </div>
            </div>

            <div className="d-flex flex-wrap align-items-center gap-2">
              <div className="d-flex align-items-center gap-1 small">
                <span className="text-muted">Radius:</span>
                <select
                  className="form-select form-select-sm"
                  style={{ width: "auto" }}
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Number(e.target.value))}
                >
                  <option value={5}>5 km</option>
                  <option value={10}>10 km</option>
                  <option value={15}>15 km</option>
                  <option value={25}>25 km</option>
                </select>
              </div>

              <select
                className="form-select form-select-sm"
                style={{ width: "auto" }}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="donors_notified">Donors Notified</option>
                <option value="fulfilled">Fulfilled</option>
                <option value="cancelled">Cancelled</option>
              </select>

              <button
                type="button"
                onClick={handleRefresh}
                className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1"
              >
                <RefreshCw size={14} /> Refresh
              </button>
            </div>
          </div>

          {loading ? (
            <LoadingSpinner text="Loading blood requests..." />
          ) : filteredRequests.length === 0 ? (
            <div className="text-center py-4 text-muted small">
              No blood requests found. Use the form to create a new request.
            </div>
          ) : (
            <div className="d-flex flex-column gap-3">
              {filteredRequests.map((req) => {
                const busy = Boolean(busyMap[req.request_id]);
                const isApproved = req.verification_status === "approved";
                const isClosed = ["fulfilled", "cancelled", "expired"].includes(req.request_status);
                const activeDrawer = openDrawer[req.request_id];
                const preview = previewMap[req.request_id];
                const responses = responsesMap[req.request_id];

                return (
                  <div key={req.request_id} className="border rounded p-3 bg-white">
                    <div className="d-flex flex-column flex-lg-row justify-content-between gap-3">
                      <div>
                        <div className="d-flex flex-wrap align-items-center gap-2 mb-2">
                          <span className="badge bg-danger fs-6">{req.blood_group}</span>
                          <StatusBadge status={req.urgency} />
                          <span className="badge bg-light text-dark border">
                            {req.units_needed} Unit(s)
                          </span>
                          <span className="small text-muted">Verification:</span>
                          <StatusBadge status={req.verification_status} />
                          <span className="small text-muted">Status:</span>
                          <StatusBadge status={req.request_status} />
                        </div>

                        <h6 className="fw-bold mb-1">{req.hospital_name}</h6>
                        <div className="d-flex flex-wrap gap-3 small text-muted">
                          <span className="d-flex align-items-center gap-1">
                            <MapPin size={14} /> {req.locality}
                          </span>
                          <span className="d-flex align-items-center gap-1">
                            <Clock size={14} /> Required By: {req.required_by_date}
                          </span>
                        </div>
                      </div>

                      <div className="d-flex flex-wrap align-items-start gap-2">
                        <button
                          type="button"
                          onClick={() => handlePreviewMatches(req.request_id)}
                          disabled={busy}
                          className="btn btn-outline-primary btn-sm d-flex align-items-center gap-1"
                        >
                          <Users size={14} /> Preview Matches
                        </button>

                        {!isClosed && (
                          <button
                            type="button"
                            onClick={() => handleDispatchDonors(req.request_id)}
                            disabled={busy || !isApproved}
                            title={
                              isApproved
                                ? "Notify eligible donors within radius"
                                : "Requires admin approval before notifying donors"
                            }
                            className="btn btn-blood btn-sm d-flex align-items-center gap-1"
                          >
                            <Send size={14} /> Notify Donors
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => handleViewResponses(req.request_id)}
                          disabled={busy}
                          className="btn btn-outline-success btn-sm d-flex align-items-center gap-1"
                        >
                          <Eye size={14} /> Responses
                        </button>

                        {req.requisition_doc_url && (
                          <button
                            type="button"
                            onClick={() =>
                              setPreviewDoc({
                                path: req.requisition_doc_url,
                                title: `Requisition Document — ${req.hospital_name}`,
                              })
                            }
                            className="btn btn-outline-dark btn-sm d-flex align-items-center gap-1"
                          >
                            <FileText size={14} /> Document
                          </button>
                        )}

                        {!isClosed && (
                          <>
                            <button
                              type="button"
                              onClick={() => handleLifecycleChange(req.request_id, "fulfilled")}
                              disabled={busy}
                              className="btn btn-success btn-sm d-flex align-items-center gap-1"
                            >
                              <CheckCircle2 size={14} /> Fulfill
                            </button>
                            <button
                              type="button"
                              onClick={() => handleLifecycleChange(req.request_id, "cancelled")}
                              disabled={busy}
                              className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1"
                            >
                              <XCircle size={14} /> Cancel
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {!isApproved && !isClosed && (
                      <div className="alert alert-warning py-2 px-3 small mt-2 mb-0">
                        Verification status is <strong>{req.verification_status}</strong>. An administrator must approve this request in the Admin Review queue before donor notifications can be dispatched.
                      </div>
                    )}

                    {activeDrawer === "preview" && preview && (
                      <div className="mt-3 pt-3 border-top bg-light p-3 rounded">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <strong className="small">
                            Eligible {preview.blood_group} Donors within {preview.search_radius_km} km:{" "}
                            {preview.total_matches}
                          </strong>
                          <button
                            type="button"
                            className="btn-close btn-sm"
                            aria-label="Close"
                            onClick={() => setOpenDrawer((p) => ({ ...p, [req.request_id]: null }))}
                          />
                        </div>
                        {preview.donors.length === 0 ? (
                          <div className="small text-muted">
                            No available {preview.blood_group} donors found within {preview.search_radius_km} km. Try increasing the radius.
                          </div>
                        ) : (
                          <div className="table-responsive">
                            <table className="table table-sm table-bordered bg-white mb-0 small">
                              <thead>
                                <tr>
                                  <th>Donor</th>
                                  <th>Locality</th>
                                  <th>Blood Group</th>
                                  <th>Distance</th>
                                </tr>
                              </thead>
                              <tbody>
                                {preview.donors.map((d) => (
                                  <tr key={d.donor_id}>
                                    <td>{d.full_name}</td>
                                    <td>{d.locality}</td>
                                    <td>{d.blood_group}</td>
                                    <td>{d.distance_km} km</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}

                    {activeDrawer === "responses" && responses && (
                      <div className="mt-3 pt-3 border-top bg-light p-3 rounded">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <strong className="small">
                            Donor Responses ({responses.length})
                          </strong>
                          <button
                            type="button"
                            className="btn-close btn-sm"
                            aria-label="Close"
                            onClick={() => setOpenDrawer((p) => ({ ...p, [req.request_id]: null }))}
                          />
                        </div>
                        {responses.length === 0 ? (
                          <div className="small text-muted">
                            No donors have been notified yet. Click "Notify Donors" once approved.
                          </div>
                        ) : (
                          <div className="d-flex flex-column gap-2">
                            {responses.map((resp) => (
                              <div
                                key={resp.response_id}
                                className="bg-white border rounded p-2 d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 small"
                              >
                                <div>
                                  <div className="d-flex align-items-center gap-2">
                                    <strong>{resp.donor_name}</strong>
                                    <StatusBadge status={resp.status} />
                                    <span className="text-muted">
                                      ({resp.donor_locality}, ~{resp.approximate_distance_km} km)
                                    </span>
                                  </div>
                                </div>
                                <div>
                                  {resp.contact_revealed && (resp.donor_phone || resp.donor_email) ? (
                                    <div className="d-flex flex-wrap gap-3 text-success fw-semibold">
                                      {resp.donor_phone && (
                                        <span className="d-flex align-items-center gap-1">
                                          <Phone size={13} /> {resp.donor_phone}
                                        </span>
                                      )}
                                      {resp.donor_email && (
                                        <span className="d-flex align-items-center gap-1">
                                          <Mail size={13} /> {resp.donor_email}
                                        </span>
                                      )}
                                    </div>
                                  ) : (
                                    <span className="text-muted d-flex align-items-center gap-1">
                                      <ShieldCheck size={13} /> Contact masked (awaiting acceptance & consent)
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
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
