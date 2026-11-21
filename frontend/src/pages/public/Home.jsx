import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Heart, ShieldCheck, MapPin, Quote } from "lucide-react";

const DONOR_QUOTES = [
  {
    text: "A single pint can save three lives — a single gesture can create a million smiles.",
    author: "Be a Voluntary Blood Donor",
  },
  {
    text: "Tears of a mother cannot save her child, but your blood can.",
    author: "Donate Blood, Gift Life",
  },
  {
    text: "You don't have to be a doctor to save a life — just roll up your sleeve.",
    author: "Every Drop Counts",
  },
];

export function Home() {
  const [quoteIdx, setQuoteIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setQuoteIdx((prev) => (prev + 1) % DONOR_QUOTES.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const currentQuote = DONOR_QUOTES[quoteIdx];

  return (
    <div>
      <section className="bg-white py-5 border-bottom">
        <div className="container py-4 text-center">
          <div className="mx-auto mb-4" style={{ maxWidth: "820px" }}>
            <Quote size={32} className="text-danger mb-3 opacity-75" />
            <h1 className="display-6 fw-bold text-dark mb-2">
              &ldquo;{currentQuote.text}&rdquo;
            </h1>
            <div className="text-danger small fw-semibold mb-4">
              &mdash; {currentQuote.author}
            </div>
          </div>

          <p className="text-muted small mx-auto mb-4" style={{ maxWidth: "680px" }}>
            RaktSetu is a real-time blood donor coordination platform connecting voluntary donors, patients, and verified hospitals. It uses locality-based Haversine proximity matching within 10 km, admin-reviewed requisition verification, and consent-gated contact sharing to help fulfill urgent blood needs safely.
          </p>

          <div className="d-flex justify-content-center gap-3">
            <Link to="/register" className="btn btn-blood btn-lg px-4">
              Register as Donor
            </Link>
            <Link to="/login" className="btn btn-outline-secondary btn-lg px-4">
              Platform Login
            </Link>
          </div>
        </div>
      </section>

      <section className="py-5 bg-light">
        <div className="container">
          <div className="row g-4 text-center">
            <div className="col-md-4">
              <div className="card card-healthcare h-100 p-4">
                <div className="mb-3 text-danger"><MapPin size={36} className="mx-auto" /></div>
                <h5 className="fw-bold">Locality Proximity Matching</h5>
                <p className="text-muted small">
                  Straight-line Haversine filtering connects requests with nearby donors across Ahmedabad localities without exposing private GPS coordinates.
                </p>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card card-healthcare h-100 p-4">
                <div className="mb-3 text-danger"><ShieldCheck size={36} className="mx-auto" /></div>
                <h5 className="fw-bold">Two-Tier Verification</h5>
                <p className="text-muted small">
                  Individual requests require administrative clinical review, while authorized hospitals submit expedited requests under trusted status.
                </p>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card card-healthcare h-100 p-4">
                <div className="mb-3 text-danger"><Heart size={36} className="mx-auto" /></div>
                <h5 className="fw-bold">Consent-Gated Privacy</h5>
                <p className="text-muted small">
                  Donors retain complete autonomy over their data. Contact numbers and emails are only revealed after an explicit acceptance decision.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
