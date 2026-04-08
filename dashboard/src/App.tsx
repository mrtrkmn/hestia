import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import FilesPage from "./pages/FilesPage";
import PipelinesPage from "./pages/PipelinesPage";
import StoragePage from "./pages/StoragePage";
import IoTPage from "./pages/IoTPage";
import AdminPage from "./pages/AdminPage";

function App() {
  return (
    <BrowserRouter>
      <nav className="app-nav">
        <span className="logo">🔥 Hestia</span>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/files">Files</NavLink>
        <NavLink to="/pipelines">Pipelines</NavLink>
        <NavLink to="/storage">Storage</NavLink>
        <NavLink to="/iot">IoT</NavLink>
        <NavLink to="/admin">Admin</NavLink>
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
