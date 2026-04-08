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

  const uptime = (s: number) => { const h = Math.floor(s / 3600); const m = Math.floor((s % 3600) / 60); return h > 0 ? `${h}h ${m}m` : `${m}m`; };

  return (
    <div className="page">
      <h1>{t("dashboard.title")}</h1>
      <h2>{t("dashboard.serviceHealth")}</h2>
      {services.length === 0 ? <div className="empty">{t("dashboard.noServices")}</div> : (
        <div className="card-grid">
          {services.map((s) => (
            <div className="card" key={s.name}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{s.name}</strong>
                <span className={`badge badge-${s.status}`}>{s.status}</span>
              </div>
              <div style={{ marginTop: 8, fontSize: 13, color: "#a0a3b1" }}>{t("dashboard.uptime")}: {uptime(s.uptime_seconds)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
