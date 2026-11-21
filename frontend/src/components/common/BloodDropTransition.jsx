import { useEffect } from "react";

export function BloodDropTransition({
  isOpen,
  onProceed,
  duration = 5500
}) {
  useEffect(() => {
    if (!isOpen) return;

    const timer = setTimeout(() => {
      onProceed();
    }, duration);

    return () => clearTimeout(timer);
  }, [isOpen, onProceed, duration]);

  if (!isOpen) return null;

  return (
    <div className="blood-transition-overlay">
      <div className="blood-drop-stage">
        
        {/* Soft Ambient Radiance */}
        <div className="blood-ambient-glow" />

        {/* Concentric Surface Liquid Ripples */}
        <div className="blood-ripple-ring" />
        <div className="blood-ripple-ring" />

        {/* Realistic Liquid Droplet */}
        <svg
          className="pure-blood-drop-svg"
          viewBox="0 0 100 130"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Deep Ruby to Crimson Gradient */}
            <radialGradient id="liquidDepth" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#ff4d4f" />
              <stop offset="35%" stopColor="#d92323" />
              <stop offset="75%" stopColor="#960d0d" />
              <stop offset="100%" stopColor="#540505" />
            </radialGradient>

            {/* Specular Curvature Highlight */}
            <linearGradient id="fluidSheen" x1="25" y1="20" x2="45" y2="85" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
              <stop offset="40%" stopColor="#ffffff" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Liquid Tear Path */}
          <path
            d="M50 4 
               C50 4, 14 62, 14 90 
               C14 111, 30 126, 50 126 
               C70 126, 86 111, 86 90 
               C86 62, 50 4, 50 4 Z"
            fill="url(#liquidDepth)"
          />

          {/* Curved Specular Reflection */}
          <path
            className="drop-fluid-sheen"
            d="M32 38 
               C23 55, 21 74, 26 90 
               C27 76, 31 62, 38 48 
               C40 44, 35 34, 32 38 Z"
            fill="url(#fluidSheen)"
          />
        </svg>

      </div>
    </div>
  );
}