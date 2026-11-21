import { useEffect, useState } from "react";
import { ArrowRight, HeartHandshake, ShieldCheck, Activity, KeyRound } from "lucide-react";

const ROLE_METADATA = {
  donor: {
    icon: HeartHandshake,
    tagClass: "donor",
    tagLabel: "Voluntary Lifesaver",
    registerTitle: "Welcome to the Lifeline Network",
    loginTitle: "Welcome Back, Voluntary Donor",
    registerQuote: "“A single donation becomes the quiet pulse of someone’s second chance.”",
    loginQuote: "“Every voluntary donor on standby makes an entire city safer.”",
    subtext: "Ahmedabad voluntary blood network active. Proximity matching standby enabled.",
    btnLabel: "Enter Donor Portal"
  },
  requester: {
    icon: Activity,
    tagClass: "requester",
    tagLabel: "Emergency Requester",
    registerTitle: "Account Registered Successfully",
    loginTitle: "Welcome Back to Requester Portal",
    registerQuote: "“In urgent hours, distance shortens through community solidarity.”",
    loginQuote: "“Tracking emergency requisitions with direct donor coordination.”",
    subtext: "Requisitions are prioritized and matched with nearby verified voluntary donors.",
    btnLabel: "Enter Requester Portal"
  },
  hospital: {
    icon: ShieldCheck,
    tagClass: "hospital",
    tagLabel: "Clinical Healthcare Partner",
    registerTitle: "Institutional Profile Initialized",
    loginTitle: "Hospital Emergency Desk Active",
    registerQuote: "“Where clinical precision connects with rapid local response.”",
    loginQuote: "“Direct access to voluntary donors within a 10 km medical radius.”",
    subtext: "Coordinate hospital requisitions and view consented donor contact details.",
    btnLabel: "Open Hospital Desk"
  },
  admin: {
    icon: KeyRound,
    tagClass: "admin",
    tagLabel: "System Administrator",
    registerTitle: "Administrative Identity Configured",
    loginTitle: "System Operations Terminal",
    registerQuote: "“Integrity, swift clinical verification, and uncompromising privacy.”",
    loginQuote: "“Monitoring real-time proximity matching and hospital credentialing.”",
    subtext: "Full oversight of audit trails, verification queues, and platform health.",
    btnLabel: "Open Control Panel"
  }
};

export function AuthWelcomeModal(props) {
  if (!props.isOpen) return null;
  return <AuthWelcomeModalContent {...props} />;
}

function AuthWelcomeModalContent({
  mode = "login", // 'login' | 'register'
  role = "donor",
  userName = "User",
  onProceed
}) {
  const [secondsLeft, setSecondsLeft] = useState(4);
  const normalizedRole = (role || "donor").toLowerCase();
  const meta = ROLE_METADATA[normalizedRole] || ROLE_METADATA.donor;
  const RoleIcon = meta.icon;

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          onProceed();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onProceed]);

  const title = mode === "register" ? meta.registerTitle : meta.loginTitle;
  const quote = mode === "register" ? meta.registerQuote : meta.loginQuote;
  const progressPercent = ((4 - secondsLeft) / 4) * 100;

  return (
    <div className="auth-modal-overlay">
      <div className="auth-modal-card text-center">
        
        {/* Minimalist Medical Pulse Vessel */}
        <div className="medical-icon-wrapper">
          <div className="medical-icon-aura" />
          <div className="medical-icon-ring">
            {/* Clean Medical Droplet with Embedded Cardiac Beat */}
            <svg
              className="medical-svg-drop"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" fill="rgba(201, 42, 42, 0.12)" />
              {/* Cardiac Pulse Line across droplet */}
              <path d="M7.5 14h2.2l1.3-2.5 1.8 4.5 1.5-3 1.2 1h1" strokeWidth="1.6" />
            </svg>
          </div>
        </div>

        {/* Role Tag */}
        <div>
          <span className={`auth-role-tag ${meta.tagClass}`}>
            <RoleIcon size={13} />
            <span>{meta.tagLabel}</span>
          </span>
        </div>

        {/* Header */}
        <h5 className="fw-bold text-dark mb-1">{userName}</h5>
        <div className="text-muted small mb-2">{title}</div>

        {/* Refined Quote Card */}
        <div className="clinical-quote-box">
          <p className="clinical-quote-text">{quote}</p>
          <p className="clinical-quote-context">{meta.subtext}</p>
        </div>

        {/* Action Button */}
        <button
          onClick={onProceed}
          className="btn btn-blood w-100 py-2 d-flex align-items-center justify-content-center gap-2 fw-semibold"
        >
          <span>{meta.btnLabel}</span>
          <ArrowRight size={16} />
        </button>

        {/* Subtle Countdown Bar */}
        <div className="auth-timer-track">
          <div
            className="auth-timer-bar"
            style={{ width: `${Math.min(progressPercent, 100)}%` }}
          />
        </div>
        <div className="text-muted text-end mt-1" style={{ fontSize: "0.72rem" }}>
          Redirecting in {secondsLeft}s
        </div>

      </div>
    </div>
  );
}