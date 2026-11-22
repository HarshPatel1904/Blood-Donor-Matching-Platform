import { Outlet } from "react-router-dom";
import { Navbar } from "../components/common/Navbar";
import { getPortalConfig } from "../utils/portalConfig";

export function MainLayout() {
  const portal = getPortalConfig();

  return (
    <>
      <Navbar />
      <main className="flex-grow-1">
        <Outlet />
      </main>
      {!portal.isDirectAdmin && (
        <footer className="py-2 text-center border-top bg-white">
          <span className="text-muted small">v1.1 &bull; Auto-Deployed via CI/CD</span>
        </footer>
      )}
    </>
  );
}
