import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "./components/LanguageSwitcher";
import DashboardPage from "./pages/DashboardPage";
import FilesPage from "./pages/FilesPage";
import PipelinesPage from "./pages/PipelinesPage";
import StoragePage from "./pages/StoragePage";
import IoTPage from "./pages/IoTPage";
import AdminPage from "./pages/AdminPage";

function App() {
  const { t } = useTranslation();

  return (
    <BrowserRouter>
      <nav className="app-nav">
        <span className="logo">🔥 Hestia</span>
        <NavLink to="/">{t("nav.dashboard")}</NavLink>
        <NavLink to="/files">{t("nav.files")}</NavLink>
        <NavLink to="/pipelines">{t("nav.pipelines")}</NavLink>
        <NavLink to="/storage">{t("nav.storage")}</NavLink>
        <NavLink to="/iot">{t("nav.iot")}</NavLink>
        <NavLink to="/admin">{t("nav.admin")}</NavLink>
        <LanguageSwitcher />
      </nav>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/files" element={<FilesPage />} />
        <Route path="/pipelines" element={<PipelinesPage />} />
        <Route path="/storage" element={<StoragePage />} />
        <Route path="/iot" element={<IoTPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
