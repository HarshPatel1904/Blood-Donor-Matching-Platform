import { useEffect, useState } from "react";
import { X, ExternalLink, Download, FileText, AlertCircle } from "lucide-react";
import { api } from "../../services/api";
import { LoadingSpinner } from "./LoadingSpinner";

/**
 * Authenticated modal previewer for requisition and hospital license documents.
 */
export function DocumentPreviewModal({ docPath, title = "Uploaded Document", onClose }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [docData, setDocData] = useState(null);

  useEffect(() => {
    let active = true;
    let createdUrl = null;

    async function loadDoc() {
      try {
        const result = await api.fetchDocumentBlob(docPath);
        if (!active) {
          URL.revokeObjectURL(result.blobUrl);
          return;
        }
        createdUrl = result.blobUrl;
        setDocData(result);
      } catch (err) {
        if (active) {
          setError(err.message || "Failed to load document.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadDoc();

    return () => {
      active = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [docPath]);

  const isImage = docData?.mimeType?.startsWith("image/");
  const isPdf =
    docData?.mimeType === "application/pdf" ||
    docData?.filename?.toLowerCase().endsWith(".pdf");

  return (
    <div
      className="modal d-block"
      tabIndex="-1"
      role="dialog"
      style={{ backgroundColor: "rgba(15, 23, 42, 0.65)", zIndex: 1060 }}
      onClick={onClose}
    >
      <div
        className="modal-dialog modal-xl modal-dialog-centered"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-content shadow-lg border-0">
          <div className="modal-header bg-dark text-white">
            <div className="d-flex align-items-center gap-2">
              <FileText size={18} className="text-danger" />
              <h6 className="modal-title mb-0 fw-bold">{title}</h6>
              {docData?.filename && (
                <span className="badge bg-secondary small">{docData.filename}</span>
              )}
            </div>
            <div className="d-flex align-items-center gap-2">
              {docData?.blobUrl && (
                <>
                  <a
                    href={docData.blobUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-outline-light btn-sm d-flex align-items-center gap-1"
                  >
                    <ExternalLink size={14} /> Open Tab
                  </a>
                  <a
                    href={docData.blobUrl}
                    download={docData.filename || "document"}
                    className="btn btn-danger btn-sm d-flex align-items-center gap-1"
                  >
                    <Download size={14} /> Download
                  </a>
                </>
              )}
              <button
                type="button"
                className="btn btn-outline-light btn-sm"
                aria-label="Close"
                onClick={onClose}
              >
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="modal-body bg-light p-3" style={{ minHeight: "65vh" }}>
            {loading && <LoadingSpinner text="Fetching authenticated document..." />}

            {!loading && error && (
              <div className="alert alert-danger d-flex align-items-center gap-2 mb-0">
                <AlertCircle size={18} className="flex-shrink-0" />
                <div>
                  <strong>Unable to preview document:</strong> {error}
                  <div className="small text-muted mt-1">Path: {docPath}</div>
                </div>
              </div>
            )}

            {!loading && !error && docData?.blobUrl && (
              <>
                {isImage ? (
                  <div className="text-center">
                    <img
                      src={docData.blobUrl}
                      alt={title}
                      className="img-fluid rounded border bg-white"
                      style={{ maxHeight: "72vh" }}
                    />
                  </div>
                ) : isPdf ? (
                  <iframe
                    src={docData.blobUrl}
                    title={title}
                    className="w-100 rounded border bg-white"
                    style={{ height: "72vh" }}
                  />
                ) : (
                  <div className="text-center py-5">
                    <p className="text-muted mb-3">
                      Inline preview is not supported for this file type ({docData.mimeType}).
                    </p>
                    <a
                      href={docData.blobUrl}
                      download={docData.filename || "document"}
                      className="btn btn-blood"
                    >
                      <Download size={16} className="me-1" /> Download Document
                    </a>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
