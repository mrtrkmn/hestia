import { useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "./components/LanguageSwitcher";
import DashboardPage from "./pages/DashboardPage";
import FilesPage from "./pages/FilesPage";
import PipelinesPage from "./pages/PipelinesPage";
import StoragePage from "./pages/StoragePage";
import IoTPage from "./pages/IoTPage";
import AdminPage from "./pages/AdminPage";

const NAV_ITEMS = [
  { to: "/", icon: "📊", key: "nav.dashboard" },
  { to: "/files", icon: "📁", key: "nav.files" },
  { to: "/pipelines", icon: "⚡", key: "nav.pipelines" },
  { to: "/storage", icon: "💾", key: "nav.storage" },
  { to: "/iot", icon: "🔌", key: "nav.iot" },
  { to: "/admin", icon: "⚙️", key: "nav.admin" },
];

function PageTitle() {
  const { t } = useTranslation();
  const loc = useLocation();
  const item = NAV_ITEMS.find((n) => n.to === loc.pathname) || NAV_ITEMS[0];
  return <h1>{t(item.key)}</h1>;
}

function App() {
  const { t } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <BrowserRouter>
      <div className="app-layout">
        <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
          <div className="sidebar-header">
            <div className="logo">
              <div className="logo-icon">🔥</div>
              Hestia
            </div>
          </div>
          <nav className="sidebar-nav">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} onClick={() => setSidebarOpen(false)}>
                <span className="nav-icon">{item.icon}</span>
                {t(item.key)}
              </NavLink>
            ))}
          </nav>
          <div className="sidebar-footer">
            <LanguageSwitcher />
          </div>
        </aside>

        <div className="main-content">
          <header className="topbar">
            <button className="mobile-toggle btn btn-ghost" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
            <PageTitle />
            <div className="text-secondary" style={{ fontSize: 12 }}>v1.0.0</div>
          </header>

          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/files" element={<FilesPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/storage" element={<StoragePage />} />
            <Route path="/iot" element={<IoTPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
