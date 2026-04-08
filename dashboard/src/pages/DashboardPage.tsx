import { useState, useEffect } from "react";
import api from "../api/client";
import type { ServiceHealth } from "../types";

export default function DashboardPage() {
  const [services, setServices] = useState<ServiceHealth[]>([]);

  useEffect(() => {
    const load = () => api.get("/services/health").then((r) => setServices(r.data.services ?? [])).catch(() => {});
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  const badge = (s: string) => `badge badge-${s}`;
  const uptime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <h2>Service Health</h2>
      {services.length === 0 ? (
        <div className="empty">No services reporting. Ensure backend is running.</div>
      ) : (
        <div className="card-grid">
          {services.map((s) => (
            <div className="card" key={s.name}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{s.name}</strong>
                <span className={badge(s.status)}>{s.status}</span>
              </div>
              <div style={{ marginTop: 8, fontSize: 13, color: "#a0a3b1" }}>
                Uptime: {uptime(s.uptime_seconds)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
