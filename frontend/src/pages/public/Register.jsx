import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { UserCheck, Building2, UserPlus } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useNotification } from "../../context/NotificationContext";
import { BloodDropTransition } from "../../components/common/BloodDropTransition";
import { getPortalConfig } from "../../utils/portalConfig";

const LOCALITIES = [
  "Navrangpura", "Satellite", "Vastrapur", "Maninagar",
  "Bopal", "Thaltej", "Chandkheda", "Paldi", "Gota", "SG Highway"
];

const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export function Register() {
  const portal = getPortalConfig();
  const [roleTab, setRoleTab] = useState(portal.role);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    phone: "",
    blood_group: "B+",
    locality: "Navrangpura",
    hospital_name: "",
    license_number: "",
    address: "",
    official_phone: "",
    license_doc: null
  });
  const [submitting, setSubmitting] = useState(false);

  // Transition state
  const [showTransition, setShowTransition] = useState(false);
  const [targetPath, setTargetPath] = useState("/donor/dashboard");

  const { registerDonor, registerRequester, registerHospital } = useAuth();
  const { notifyError } = useNotification();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, files } = e.target;
    if (type === "file") {
      setFormData({ ...formData, [name]: files?.[0] || null });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (roleTab === "donor") {
        await registerDonor({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          phone: formData.phone,
          blood_group: formData.blood_group,
          locality: formData.locality,
          city: "Ahmedabad"
        });
        setTargetPath("/donor/dashboard");
        setShowTransition(true);
      } else if (roleTab === "requester") {
        await registerRequester({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          phone: formData.phone
        });
        setTargetPath("/requester/dashboard");
        setShowTransition(true);
      } else if (roleTab === "hospital") {
        let hospitalPayload;
        if (formData.license_doc) {
          const fd = new FormData();
          fd.append("email", formData.email);
          fd.append("password", formData.password);
          fd.append("contact_person", formData.full_name);
          fd.append("phone", formData.phone);
          fd.append("hospital_name", formData.hospital_name);
          fd.append("license_number", formData.license_number);
          fd.append("address", formData.address);
          fd.append("locality", formData.locality);
          fd.append("official_phone", formData.official_phone);
          fd.append("license_doc", formData.license_doc);
          hospitalPayload = fd;
        } else {
          hospitalPayload = {
            email: formData.email,
            password: formData.password,
            contact_person: formData.full_name,
            phone: formData.phone,
            hospital_name: formData.hospital_name,
            license_number: formData.license_number,
            address: formData.address,
            locality: formData.locality,
            official_phone: formData.official_phone
          };
        }
        await registerHospital(hospitalPayload);
        setTargetPath("/hospital/dashboard");
        setShowTransition(true);
      }
    } catch (err) {
      notifyError(err.message || "Registration failed.");
      setSubmitting(false);
    }
  };

  const handleProceed = () => {
    setShowTransition(false);
    navigate(targetPath);
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
        <div className="col-md-8 col-lg-7">
          <div className="card card-healthcare p-4 p-md-5">
            <div className="text-center mb-4">
              <h3 className="fw-bold">Create Platform Account</h3>
              <p className="text-muted small">Select your role to complete profile registration</p>
            </div>

            <ul className="nav nav-pills nav-fill mb-4">
              <li className="nav-item">
                <button
                  type="button"
                  className={`nav-link ${roleTab === "donor" ? "active bg-danger text-white" : "text-dark"}`}
                  onClick={() => setRoleTab("donor")}
                >
                  <UserPlus size={16} className="me-1" /> Voluntary Donor
                </button>
              </li>
              <li className="nav-item">
                <button
                  type="button"
                  className={`nav-link ${roleTab === "requester" ? "active bg-danger text-white" : "text-dark"}`}
                  onClick={() => setRoleTab("requester")}
                >
                  <UserCheck size={16} className="me-1" /> Individual Requester
                </button>
              </li>
              <li className="nav-item">
                <button
                  type="button"
                  className={`nav-link ${roleTab === "hospital" ? "active bg-danger text-white" : "text-dark"}`}
                  onClick={() => setRoleTab("hospital")}
                >
                  <Building2 size={16} className="me-1" /> Hospital Staff
                </button>
              </li>
            </ul>

            <form onSubmit={handleSubmit}>
              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label small fw-semibold">
                    {roleTab === "hospital" ? "Contact Person Name" : "Full Name"}
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    className="form-control"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label small fw-semibold">Personal Mobile Number</label>
                  <input
                    type="tel"
                    name="phone"
                    placeholder="+919876543210"
                    className="form-control"
                    value={formData.phone}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label small fw-semibold">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    className="form-control"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="col-md-6">
                  <label className="form-label small fw-semibold">Password</label>
                  <input
                    type="password"
                    name="password"
                    className="form-control"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </div>

                {roleTab === "donor" && (
                  <>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Blood Group</label>
                      <select
                        name="blood_group"
                        className="form-select"
                        value={formData.blood_group}
                        onChange={handleChange}
                      >
                        {BLOOD_GROUPS.map((bg) => (
                          <option key={bg} value={bg}>{bg}</option>
                        ))}
                      </select>
                    </div>

                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Locality (Ahmedabad)</label>
                      <select
                        name="locality"
                        className="form-select"
                        value={formData.locality}
                        onChange={handleChange}
                      >
                        {LOCALITIES.map((loc) => (
                          <option key={loc} value={loc}>{loc}</option>
                        ))}
                      </select>
                    </div>
                  </>
                )}

                {roleTab === "hospital" && (
                  <>
                    <div className="col-12">
                      <label className="form-label small fw-semibold">Hospital Legal Name</label>
                      <input
                        type="text"
                        name="hospital_name"
                        className="form-control"
                        value={formData.hospital_name}
                        onChange={handleChange}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">License / Registration Number</label>
                      <input
                        type="text"
                        name="license_number"
                        placeholder="GJ-AHM-HOSP-..."
                        className="form-control"
                        value={formData.license_number}
                        onChange={handleChange}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Official Desk Phone</label>
                      <input
                        type="tel"
                        name="official_phone"
                        placeholder="+917926000000"
                        className="form-control"
                        value={formData.official_phone}
                        onChange={handleChange}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Locality (Ahmedabad)</label>
                      <select
                        name="locality"
                        className="form-select"
                        value={formData.locality}
                        onChange={handleChange}
                      >
                        {LOCALITIES.map((loc) => (
                          <option key={loc} value={loc}>{loc}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Address Details</label>
                      <input
                        type="text"
                        name="address"
                        className="form-control"
                        value={formData.address}
                        onChange={handleChange}
                        required
                      />
                    </div>
                    <div className="col-12">
                      <label className="form-label small fw-semibold">
                        Hospital License Document <span className="text-muted fw-normal">(PDF/PNG/JPG for Admin verification)</span>
                      </label>
                      <input
                        type="file"
                        name="license_doc"
                        accept=".pdf,.png,.jpg,.jpeg"
                        className="form-control"
                        onChange={handleChange}
                      />
                    </div>
                  </>
                )}

                <div className="col-12 mt-4">
                  <button type="submit" className="btn btn-blood w-100 py-2 fw-semibold" disabled={submitting}>
                    {submitting ? "Submitting..." : "Complete Registration"}
                  </button>
                </div>
              </div>
            </form>

            <div className="mt-4 pt-3 border-top text-center small text-muted">
              Already registered? <Link to="/login" className="text-danger fw-semibold">Log in</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}