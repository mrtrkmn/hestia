import { useState, useEffect } from "react";
import api from "../api/client";
import type { ServiceHealth } from "../types";

export default function ServiceCatalog() {
  const [services, setServices] = useState<ServiceHealth[]>([]);

  useEffect(() => {
    const load = () =>
      api.get("/services/health").then((r) => setServices(r.data.services ?? [])).catch(() => {});
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  const color = (s: string) =>
    s === "healthy" ? "green" : s === "degraded" ? "orange" : "red";

  return (
    <div>
      <h2>Services</h2>
      {services.length === 0 && <p>No services reporting.</p>}
      <ul>
        {services.map((s) => (
          <li key={s.name} style={{ color: color(s.status) }}>
            {s.name}: {s.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
