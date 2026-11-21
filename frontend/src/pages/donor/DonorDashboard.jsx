import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  HeartHandshake,
  MapPin,
  CheckCircle2,
  XCircle,
  Calendar,
  ShieldCheck,
  Save,
  Radio,
  Power,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useNotification } from "../../context/NotificationContext";
import { api } from "../../services/api";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { BLOOD_GROUPS, DEFAULT_LOCALITIES } from "../../utils/constants";

export function DonorDashboard() {
  const { user, refreshProfile } = useAuth();
  const { notifySuccess, notifyError } = useNotification();

  const [profile, setProfile] = useState(null);
  const [localities, setLocalities] = useState(DEFAULT_LOCALITIES);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [incomingCount, setIncomingCount] = useState(0);

  const [editForm, setEditForm] = useState({
    blood_group: "B+",
    locality: "Navrangpura",
    consent_share_contact: true,
    email_notifications: true,
    last_donated_date: "",
  });

  // Fetch live donor profile and active matched requests on mount
  useEffect(() => {
    async function loadDonorData() {
      try {
        const [profileRes, requestsRes, locRes] = await Promise.all([
          api.get("/donors/profile"),
          api.get("/donors/matching-requests"),
          api.get("/localities").catch(() => null),
        ]);

        if (profileRes.success && profileRes.data) {
          const p = profileRes.data;
          setProfile(p);
          setEditForm({
            blood_group: p.blood_group || "B+",
            locality: p.locality || "Navrangpura",
            consent_share_contact: p.consent_share_contact === 1,
            email_notifications: p.email_notifications === 1,
            last_donated_date: p.last_donated_date || "",
          });
        }
        if (requestsRes.success) {
          const pending = requestsRes.data.filter((r) => r.response_status === "pending");
          setIncomingCount(pending.length);
        }
        if (locRes?.success && Array.isArray(locRes.data) && locRes.data.length > 0) {
          setLocalities(locRes.data.map((l) => l.name));
        }
      } catch (err) {
        notifyError(err.message || "Failed to load donor profile.");
      } finally {
        setLoading(false);
      }
    }

    loadDonorData();
  }, [notifyError]);

  // Toggle donor readiness (is_available: 1 vs 0)
  const handleAvailabilityToggle = async () => {
    if (!profile) return;

    const nextStatus = profile.is_available === 1 ? false : true;
    setToggling(true);

    try {
      const res = await api.patch("/donors/availability", {
        is_available: nextStatus,
      });

      if (res.success) {
        setProfile((prev) => ({
          ...prev,
          is_available: nextStatus ? 1 : 0,
        }));

        if (nextStatus) {
          notifySuccess("You are now marked as AVAILABLE for emergency blood matching.");
        } else {
          notifySuccess("Availability paused. You will not receive new emergency alerts.");
        }

        if (refreshProfile) {
          refreshProfile();
        }
      }
    } catch (err) {
      notifyError(err.message || "Failed to update availability status.");
    } finally {
      setToggling(false);
    }
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const res = await api.put("/donors/profile", {
        blood_group: editForm.blood_group,
        locality: editForm.locality,
        consent_share_contact: editForm.consent_share_contact,
        email_notifications: editForm.email_notifications,
        last_donated_date: editForm.last_donated_date || null,
      });
      if (res.success && res.data) {
        setProfile(res.data);
        notifySuccess(res.message || "Donor preferences updated.");
        if (refreshProfile) {
          refreshProfile();
        }
      }
    } catch (err) {
      notifyError(err.message || "Failed to update donor profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading donor dashboard..." />;
  }

  const isAvailable = profile?.is_available === 1;

  return (
    <div>
      {/* Top Header Banner */}
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-0 text-dark">
            Welcome back, <span className="text-danger">{profile?.full_name || user?.full_name}</span>
          </h1>
        </div>

        <Link
          to="/donor/matching-requests"
          className="btn btn-blood d-flex align-items-center justify-content-center gap-2 position-relative px-3 py-2"
        >
          <HeartHandshake size={18} />
          <span>Review Matching Requests</span>
          {incomingCount > 0 && (
            <span className="badge bg-white text-danger fw-bold rounded-pill ms-1">
              {incomingCount} New
            </span>
          )}
        </Link>
      </div>

      {/* Primary Availability Status Card */}
      <div className={`card card-healthcare border-2 mb-4 p-4 ${isAvailable ? "border-success bg-white" : "border-warning bg-white"}`}>
        <div className="row align-items-center g-3">
          <div className="col-lg-8">
            <div className="d-flex align-items-center gap-3">
              {isAvailable ? (
                <div className="rounded-circle p-2 bg-success text-white d-flex align-items-center justify-content-center">
                  <CheckCircle2 size={24} />
                </div>
              ) : (
                <div className="rounded-circle p-2 bg-warning text-dark d-flex align-items-center justify-content-center">
                  <XCircle size={24} />
                </div>
              )}
              <div>
                <h5 className="fw-bold mb-0">
                  {isAvailable ? (
                    <span className="text-success">You are ready to donate</span>
                  ) : (
                    <span className="text-muted">You are not available</span>
                  )}
                </h5>
              </div>
            </div>
          </div>

          <div className="col-lg-4 text-lg-end">
            <button
              onClick={handleAvailabilityToggle}
              disabled={toggling}
              className={`btn btn-availability-pill d-inline-flex align-items-center gap-2 px-4 py-2 ${
                isAvailable ? "btn-availability-live" : "btn-availability-paused"
              }`}
            >
              {toggling ? (
                <span className="spinner-border spinner-border-sm" role="status" />
              ) : isAvailable ? (
                <span className="status-pulse-dot" />
              ) : (
                <Radio size={18} />
              )}
              <span>{isAvailable ? "Pause Availability" : "Go Live to Donate"}</span>
              <Power size={16} className="ms-1 opacity-75" />
            </button>
          </div>
        </div>
      </div>

      {/* Profile Overview Details */}
      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <div className="card card-healthcare h-100 p-3">
            <div className="d-flex align-items-center gap-2 text-muted small mb-1">
              <MapPin size={16} className="text-danger" />
              <span>Registered Locality</span>
            </div>
            <h5 className="fw-bold mb-1 text-dark">
              {profile?.locality || "Ahmedabad"}
            </h5>
            <div className="text-muted small">
              Lat: {profile?.latitude?.toFixed(4)}, Lon: {profile?.longitude?.toFixed(4)}
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card card-healthcare h-100 p-3">
            <div className="d-flex align-items-center gap-2 text-muted small mb-1">
              <ShieldCheck size={16} className="text-primary" />
              <span>Contact Privacy Setting</span>
            </div>
            <h5 className="fw-bold mb-1 text-dark">
              {profile?.consent_share_contact === 1 ? "Consent-Gated" : "Always Anonymous"}
            </h5>
            <div className="text-muted small">
              Contact numbers are revealed only after explicit acceptance.
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card card-healthcare h-100 p-3">
            <div className="d-flex align-items-center gap-2 text-muted small mb-1">
              <Calendar size={16} className="text-success" />
              <span>Last Recorded Donation</span>
            </div>
            <h5 className="fw-bold mb-1 text-dark">
              {profile?.last_donated_date || "Not Recorded"}
            </h5>
            <div className="text-muted small">
              Recommended interval: 90 days between donations.
            </div>
          </div>
        </div>
      </div>

      {/* Update Donor Preferences */}
      <div className="card card-healthcare p-4">
        <h5 className="fw-bold mb-3">Update Donor Profile & Preferences</h5>
        <form onSubmit={handleProfileSave}>
          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label small fw-semibold">Blood Group</label>
              <select
                className="form-select"
                value={editForm.blood_group}
                onChange={(e) => setEditForm((p) => ({ ...p, blood_group: e.target.value }))}
              >
                {BLOOD_GROUPS.map((bg) => (
                  <option key={bg} value={bg}>
                    {bg}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label small fw-semibold">Locality (Ahmedabad)</label>
              <select
                className="form-select"
                value={editForm.locality}
                onChange={(e) => setEditForm((p) => ({ ...p, locality: e.target.value }))}
              >
                {localities.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label small fw-semibold">Last Donated Date</label>
              <input
                type="date"
                className="form-control"
                value={editForm.last_donated_date}
                onChange={(e) => setEditForm((p) => ({ ...p, last_donated_date: e.target.value }))}
              />
            </div>

            <div className="col-md-6">
              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="consentDefaultSwitch"
                  checked={editForm.consent_share_contact}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, consent_share_contact: e.target.checked }))
                  }
                />
                <label className="form-check-label small fw-semibold" htmlFor="consentDefaultSwitch">
                  Allow sharing contact details when I accept a request
                </label>
              </div>
            </div>

            <div className="col-md-6">
              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="emailNotifSwitch"
                  checked={editForm.email_notifications}
                  onChange={(e) =>
                    setEditForm((p) => ({ ...p, email_notifications: e.target.checked }))
                  }
                />
                <label className="form-check-label small fw-semibold" htmlFor="emailNotifSwitch">
                  Receive emergency matching notifications
                </label>
              </div>
            </div>

            <div className="col-12">
              <button
                type="submit"
                disabled={savingProfile}
                className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1 px-3"
              >
                <Save size={15} /> {savingProfile ? "Saving..." : "Save Preferences"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
