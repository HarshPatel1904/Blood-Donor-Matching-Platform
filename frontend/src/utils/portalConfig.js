const PORTAL_BY_PORT = {
  "5173": {
    role: "donor",
    label: "Donor Portal",
    tabTitle: "RaktSetu — Donor Portal",
    isDirectAdmin: false,
  },
  "5174": {
    role: "requester",
    label: "Individual Portal",
    tabTitle: "RaktSetu — Individual Portal",
    isDirectAdmin: false,
  },
  "5175": {
    role: "hospital",
    label: "Hospital Staff Portal",
    tabTitle: "RaktSetu — Hospital Staff Portal",
    isDirectAdmin: false,
  },
  "5176": {
    role: "admin",
    label: "Admin Portal",
    tabTitle: "RaktSetu — Admin Portal",
    isDirectAdmin: true,
  },
};

/**
 * Resolve portal metadata based on Vite mode, hostname, or port so each role
 * works identically in both multi-port local dev and dedicated S3 deployments.
 */
export function getPortalConfig() {
  const mode = import.meta.env.VITE_PORTAL_MODE;
  const port = typeof window !== "undefined" ? window.location.port : "";
  const hostname =
    typeof window !== "undefined" ? window.location.hostname.toLowerCase() : "";

  if (mode === "admin" || port === "5176" || hostname.includes("admin")) {
    return PORTAL_BY_PORT["5176"];
  }

  return (
    PORTAL_BY_PORT[port] || {
      role: "donor",
      label: "Platform Portal",
      tabTitle: "RaktSetu — Blood Donor Platform",
      isDirectAdmin: false,
    }
  );
}
