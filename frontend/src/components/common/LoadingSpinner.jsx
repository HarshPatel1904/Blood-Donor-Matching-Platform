export function LoadingSpinner({ text = "Loading platform data..." }) {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center p-5 min-vh-50">
      <div className="spinner-border text-danger" style={{ width: "3rem", height: "3rem" }} role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
      {text && <p className="mt-3 text-muted small fw-medium">{text}</p>}
    </div>
  );
}