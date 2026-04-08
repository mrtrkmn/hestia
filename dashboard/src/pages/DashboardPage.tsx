import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { ServiceHealth } from "../types";

export default function DashboardPage() {
  const { t } = useTranslation();
  const [services, setServices] = useState<ServiceHealth[]>([]);

  useEffect(() => {
    const load = () => api.get("/services/health").then((r) => setServices(r.data.services ?? [])).catch(() => {});
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  const uptime = (s: number) => {
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    if (d > 0) return `${d}d ${h}h`;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  const healthy = services.filter((s) => s.status === "healthy").length;
  const total = services.length;

  return (
    <div className="page">
      {total > 0 && (
        <div className="card-grid" style={{ marginBottom: 28 }}>
          <div className="stat-card"><div className="stat-label">Total Services</div><div className="stat-value">{total}</div></div>
          <div className="stat-card"><div className="stat-label">Healthy</div><div className="stat-value" style={{ color: "#22c55e" }}>{healthy}</div></div>
          <div className="stat-card"><div className="stat-label">Issues</div><div className="stat-value" style={{ color: total - healthy > 0 ? "#ef4444" : "#22c55e" }}>{total - healthy}</div></div>
        </div>
      )}

      <h2>{t("dashboard.serviceHealth")}</h2>
      {services.length === 0 ? (
        <div className="empty"><div className="empty-icon">📡</div>{t("dashboard.noServices")}</div>
      ) : (
        <div className="card-grid">
          {services.map((s) => (
            <div className="stat-card" key={s.name}>
              <div className="flex justify-between items-center">
                <strong style={{ fontSize: 14 }}>{s.name}</strong>
                <span className={`badge badge-${s.status}`}>{s.status}</span>
              </div>
              <div style={{ marginTop: 10, fontSize: 12, color: "#4a5178" }}>
                {t("dashboard.uptime")}: <span style={{ color: "#7b83a6" }}>{uptime(s.uptime_seconds)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
