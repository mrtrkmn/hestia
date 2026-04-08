import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { User, LogEntry } from "../types";

export default function AdminPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"users"|"logs">("users");
  const [users, setUsers] = useState<User[]>([]); const [logs, setLogs] = useState<LogEntry[]>([]);
  const [username, setUsername] = useState(""); const [email, setEmail] = useState(""); const [role, setRole] = useState<"admin"|"user">("user");

  const loadUsers = () => api.get("/admin/users").then((r) => setUsers(r.data.users ?? [])).catch(() => {});
  const loadLogs = () => api.get("/admin/logs").then((r) => setLogs(r.data.logs ?? [])).catch(() => {});
  useEffect(() => { loadUsers(); loadLogs(); }, []);

  const createUser = async () => { if (!username.trim()) return; await api.post("/admin/users", { username, email, role }); setUsername(""); setEmail(""); setRole("user"); loadUsers(); };
  const removeUser = async (id: string) => { await api.delete(`/admin/users/${id}`); loadUsers(); };

  return (
    <div className="page">
      <div className="tabs">
        <button className={`tab-btn ${tab === "users" ? "active" : ""}`} onClick={() => setTab("users")}>{t("admin.users")}</button>
        <button className={`tab-btn ${tab === "logs" ? "active" : ""}`} onClick={() => setTab("logs")}>{t("admin.logs")}</button>
      </div>

      {tab === "users" && (<>
        <div className="card">
          <h2 className="mt-0">{t("admin.createUser")}</h2>
          <div className="form-row">
            <div className="form-group"><label>{t("admin.username")}</label><input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="johndoe" /></div>
            <div className="form-group"><label>{t("admin.email")}</label><input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="john@example.com" /></div>
            <div className="form-group"><label>{t("admin.role")}</label><select value={role} onChange={(e) => setRole(e.target.value as "admin"|"user")}><option value="user">User</option><option value="admin">Admin</option></select></div>
          </div>
          <button className="btn btn-primary" onClick={createUser}>{t("admin.createBtn")}</button>
        </div>
        {users.length === 0 ? <div className="empty"><div className="empty-icon">👤</div>{t("admin.noUsers")}</div> : (
          <table><thead><tr><th>{t("admin.username")}</th><th>{t("admin.email")}</th><th>{t("admin.role")}</th><th>{t("admin.twoFactor")}</th><th></th></tr></thead>
            <tbody>{users.map((u) => (
              <tr key={u.id}><td><strong>{u.username}</strong></td><td className="text-secondary">{u.email}</td><td><span className={`badge badge-${u.role}`}>{u.role}</span></td><td>{u.totp_enabled ? "✓" : "—"}</td><td><button className="btn btn-sm btn-danger" onClick={() => removeUser(u.id)}>{t("admin.delete")}</button></td></tr>
            ))}</tbody></table>
        )}
      </>)}

      {tab === "logs" && (<>
        {logs.length === 0 ? <div className="empty"><div className="empty-icon">📋</div>{t("admin.noLogs")}</div> : (
          <table><thead><tr><th>{t("admin.time")}</th><th>{t("admin.event")}</th><th>{t("admin.user")}</th><th>{t("admin.sourceIp")}</th><th>{t("admin.resource")}</th><th>{t("admin.details")}</th></tr></thead>
            <tbody>{logs.map((l, i) => (
              <tr key={i}><td className="mono" style={{ whiteSpace: "nowrap" }}>{new Date(l.timestamp).toLocaleString()}</td><td><span className="badge badge-failed">{l.event_type}</span></td><td>{l.user}</td><td className="mono">{l.source_ip}</td><td className="text-secondary">{l.resource}</td><td className="text-muted" style={{ fontSize: 12 }}>{l.details}</td></tr>
            ))}</tbody></table>
        )}
      </>)}
    </div>
  );
}
