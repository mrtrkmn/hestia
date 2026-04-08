import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import FilesPage from "./pages/FilesPage";
import AdminPage from "./pages/AdminPage";

function App() {
  return (
    <BrowserRouter>
      <nav style={{ display: "flex", gap: 16, padding: 16, borderBottom: "1px solid #ccc" }}>
        <Link to="/">Dashboard</Link>
        <Link to="/files">Files</Link>
        <Link to="/admin">Admin</Link>
      </nav>
      <main style={{ padding: 16, maxWidth: 1200, margin: "0 auto" }}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/files" element={<FilesPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
