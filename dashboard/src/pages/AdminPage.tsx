import { useState, useEffect } from "react";
import api from "../api/client";
import type { User, LogEntry } from "../types";

export default function AdminPage() {
  const [tab, setTab] = useState<"users" | "logs">("users");
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"admin" | "user">("user");

  const loadUsers = () => api.get("/admin/users").then((r) => setUsers(r.data.users ?? [])).catch(() => {});
  const loadLogs = () => api.get("/admin/logs").then((r) => setLogs(r.data.logs ?? [])).catch(() => {});

  useEffect(() => { loadUsers(); loadLogs(); }, []);

  const createUser = async () => {
    if (!username.trim()) return;
    await api.post("/admin/users", { username, email, role });
    setUsername(""); setEmail(""); setRole("user");
    loadUsers();
  };

  const removeUser = async (id: string) => { await api.delete(`/admin/users/${id}`); loadUsers(); };

  const tabStyle = (t: string) => ({
    padding: "8px 16px", cursor: "pointer", borderBottom: tab === t ? "2px solid #4f5bff" : "2px solid transparent",
    color: tab === t ? "#e1e1e6" : "#a0a3b1", background: "none", border: "none", fontSize: 14, fontWeight: 500 as const,
  });

  return (
    <div className="page">
      <h1>Admin</h1>
      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid #2a2d3a", marginBottom: 20 }}>
        <button style={tabStyle("users")} onClick={() => setTab("users")}>Users</button>
        <button style={tabStyle("logs")} onClick={() => setTab("logs")}>System Logs</button>
      </div>

      {tab === "users" && (<>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Create User</h2>
          <div className="form-row">
            <div className="form-group"><label>Username</label><input value={username} onChange={(e) => setUsername(e.target.value)} /></div>
            <div className="form-group"><label>Email</label><input value={email} onChange={(e) => setEmail(e.target.value)} type="email" /></div>
            <div className="form-group"><label>Role</label>
              <select value={role} onChange={(e) => setRole(e.target.value as "admin" | "user")}>
                <option value="user">User</option><option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <button className="btn btn-primary" onClick={createUser}>Create user</button>
        </div>
        <h2>Users</h2>
        {users.length === 0 ? <div className="empty">No users found.</div> : (
          <table><thead><tr><th>Username</th><th>Email</th><th>Role</th><th>2FA</th><th></th></tr></thead>
            <tbody>{users.map((u) => (
              <tr key={u.id}><td><strong>{u.username}</strong></td><td>{u.email}</td><td><span className={`badge badge-${u.role}`}>{u.role}</span></td><td>{u.totp_enabled ? "✓" : "—"}</td><td><button className="btn btn-sm btn-danger" onClick={() => removeUser(u.id)}>Delete</button></td></tr>
            ))}</tbody></table>
        )}
      </>)}

      {tab === "logs" && (<>
        <h2>Security Events</h2>
        {logs.length === 0 ? <div className="empty">No log entries.</div> : (
          <table><thead><tr><th>Time</th><th>Event</th><th>User</th><th>Source IP</th><th>Resource</th><th>Details</th></tr></thead>
            <tbody>{logs.map((l, i) => (
              <tr key={i}><td style={{ fontSize: 12, whiteSpace: "nowrap" }}>{new Date(l.timestamp).toLocaleString()}</td><td><span className="badge badge-failed">{l.event_type}</span></td><td>{l.user}</td><td style={{ fontFamily: "monospace", fontSize: 12 }}>{l.source_ip}</td><td>{l.resource}</td><td style={{ fontSize: 12, color: "#a0a3b1" }}>{l.details}</td></tr>
            ))}</tbody></table>
        )}
      </>)}
    </div>
  );
}
