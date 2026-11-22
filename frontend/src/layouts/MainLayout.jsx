import { Outlet } from "react-router-dom";
import { Navbar } from "../components/common/Navbar";

export function MainLayout() {
  return (
    <>
      <Navbar />
      <main className="flex-grow-1">
        <Outlet />
      </main>
    </>
  );
}
