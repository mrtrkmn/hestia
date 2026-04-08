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

  const tabStyle = (active: boolean) => ({ padding: "8px 16px", cursor: "pointer", borderBottom: active ? "2px solid #4f5bff" : "2px solid transparent", color: active ? "#e1e1e6" : "#a0a3b1", background: "none", border: "none", fontSize: 14, fontWeight: 500 as const });

  return (
    <div className="page">
      <h1>{t("admin.title")}</h1>
      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid #2a2d3a", marginBottom: 20 }}>
        <button style={tabStyle(tab === "users")} onClick={() => setTab("users")}>{t("admin.users")}</button>
        <button style={tabStyle(tab === "logs")} onClick={() => setTab("logs")}>{t("admin.logs")}</button>
      </div>
      {tab === "users" && (<>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t("admin.createUser")}</h2>
          <div className="form-row">
            <div className="form-group"><label>{t("admin.username")}</label><input value={username} onChange={(e) => setUsername(e.target.value)} /></div>
            <div className="form-group"><label>{t("admin.email")}</label><input value={email} onChange={(e) => setEmail(e.target.value)} type="email" /></div>
            <div className="form-group"><label>{t("admin.role")}</label><select value={role} onChange={(e) => setRole(e.target.value as "admin"|"user")}><option value="user">User</option><option value="admin">Admin</option></select></div>
          </div>
          <button className="btn btn-primary" onClick={createUser}>{t("admin.createBtn")}</button>
        </div>
        <h2>{t("admin.users")}</h2>
        {users.length === 0 ? <div className="empty">{t("admin.noUsers")}</div> : (
          <table><thead><tr><th>{t("admin.username")}</th><th>{t("admin.email")}</th><th>{t("admin.role")}</th><th>{t("admin.twoFactor")}</th><th></th></tr></thead>
            <tbody>{users.map((u) => (
              <tr key={u.id}><td><strong>{u.username}</strong></td><td>{u.email}</td><td><span className={`badge badge-${u.role}`}>{u.role}</span></td><td>{u.totp_enabled ? "✓" : "—"}</td><td><button className="btn btn-sm btn-danger" onClick={() => removeUser(u.id)}>{t("admin.delete")}</button></td></tr>
            ))}</tbody></table>
        )}
      </>)}
      {tab === "logs" && (<>
        <h2>{t("admin.securityEvents")}</h2>
        {logs.length === 0 ? <div className="empty">{t("admin.noLogs")}</div> : (
          <table><thead><tr><th>{t("admin.time")}</th><th>{t("admin.event")}</th><th>{t("admin.user")}</th><th>{t("admin.sourceIp")}</th><th>{t("admin.resource")}</th><th>{t("admin.details")}</th></tr></thead>
            <tbody>{logs.map((l, i) => (
              <tr key={i}><td style={{ fontSize: 12, whiteSpace: "nowrap" }}>{new Date(l.timestamp).toLocaleString()}</td><td><span className="badge badge-failed">{l.event_type}</span></td><td>{l.user}</td><td style={{ fontFamily: "monospace", fontSize: 12 }}>{l.source_ip}</td><td>{l.resource}</td><td style={{ fontSize: 12, color: "#a0a3b1" }}>{l.details}</td></tr>
            ))}</tbody></table>
        )}
      </>)}
    </div>
  );
}
