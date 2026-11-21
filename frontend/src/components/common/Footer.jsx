import { AlertTriangle, ShieldCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-white border-top py-4 mt-auto">
      <div className="container">
        <div className="alert alert-warning d-flex align-items-start gap-2 py-2 px-3 mb-3 small" role="alert">
          <AlertTriangle size={18} className="text-warning flex-shrink-0 mt-1" />
          <div>
            <strong>Emergency Medical Disclaimer:</strong> RaktSetu is a cloud-based donor coordination and proximity matching platform. It does not provide medical diagnosis, compatibility matching, or blood collection services. In critical emergencies, contact the nearest licensed hospital blood bank immediately.
          </div>
        </div>
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-center gap-2 small text-muted">
          <div>
            &copy; 2026 RaktSetu Blood Platform. MTech Cloud Computing Project.
          </div>
          <div className="d-flex align-items-center gap-3">
            <span className="d-flex align-items-center gap-1 text-success">
              <ShieldCheck size={16} /> AWS Learner Lab Architecture Ready
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}