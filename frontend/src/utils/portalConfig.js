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
 * Resolve portal metadata based on the current Vite server port so each role
 * runs on an isolated origin and tab label.
 */
export function getPortalConfig() {
  const port = typeof window !== "undefined" ? window.location.port : "";
  return (
    PORTAL_BY_PORT[port] || {
      role: "donor",
      label: "Platform Portal",
      tabTitle: "RaktSetu — Blood Donor Platform",
      isDirectAdmin: false,
    }
  );
}
