import { Link } from "react-router-dom";
import { ShieldX } from "lucide-react";

export function Unauthorized() {
  return (
    <div className="container py-5 text-center">
      <div className="py-5">
        <ShieldX size={64} className="text-danger mb-3" />
        <h2 className="fw-bold">403 - Access Denied</h2>
        <p className="text-muted">You do not possess the role permissions required to view this portal.</p>
        <Link to="/" className="btn btn-blood mt-2">
          Return to Platform Home
        </Link>
      </div>
    </div>
  );
}