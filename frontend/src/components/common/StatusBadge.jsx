export function StatusBadge({ status }) {
  const normalized = (status || "").toLowerCase();

  let bgClass;
  let label = status || "Unknown";

  switch (normalized) {
    case "verified":
    case "approved":
    case "accepted":
    case "fulfilled":
      bgClass = "bg-success text-white";
      break;
    case "pending":
    case "on_hold":
      bgClass = "bg-warning text-dark";
      break;
    case "open":
    case "donors_notified":
      bgClass = "bg-primary text-white";
      break;
    case "urgent":
      bgClass = "bg-warning text-dark fw-bold";
      break;
    case "critical":
    case "rejected":
    case "declined":
    case "cancelled":
      bgClass = "bg-danger text-white";
      break;
    case "unavailable":
    case "expired":
      bgClass = "bg-secondary text-white";
      break;
    default:
      bgClass = "bg-light text-dark border";
  }

  return (
    <span className={`badge rounded-pill px-2 py-1 small text-uppercase ${bgClass}`}>
      {label.replace("_", " ")}
    </span>
  );
}