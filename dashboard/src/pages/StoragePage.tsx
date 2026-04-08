import { useState, useEffect } from "react";
import api from "../api/client";
import type { StorageShare } from "../types";

export default function StoragePage() {
  const [shares, setShares] = useState<StorageShare[]>([]);
  const [name, setName] = useState("");
  const [path, setPath] = useState("/srv/storage/");
  const [users, setUsers] = useState("");
  const [readOnly, setReadOnly] = useState(false);

  const load = () => api.get("/storage/shares").then((r) => setShares(r.data.shares ?? [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    await api.post("/storage/shares", {
      name, path, protocols: ["smb"],
      allowed_users: users.split(",").map((u) => u.trim()).filter(Boolean),
      read_only: readOnly,
    });
    setName(""); setPath("/srv/storage/"); setUsers(""); setReadOnly(false);
    load();
  };

  const remove = async (id: string) => { await api.delete(`/storage/shares/${id}`); load(); };

  return (
    <div className="page">
      <h1>Storage</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Create Share</h2>
        <div className="form-row">
          <div className="form-group"><label>Share name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="family-photos" /></div>
          <div className="form-group"><label>Path</label><input value={path} onChange={(e) => setPath(e.target.value)} /></div>
        </div>
        <div className="form-row">
          <div className="form-group"><label>Allowed users (comma-separated)</label><input value={users} onChange={(e) => setUsers(e.target.value)} placeholder="alex, sam" /></div>
          <div className="form-group"><label>Read only</label><label className="toggle" style={{ marginTop: 4 }}><input type="checkbox" checked={readOnly} onChange={(e) => setReadOnly(e.target.checked)} /><span className="slider" /></label></div>
        </div>
        <button className="btn btn-primary" onClick={create}>Create share</button>
      </div>
      <h2>Shares</h2>
      {shares.length === 0 ? <div className="empty">No shares configured.</div> : (
        <table><thead><tr><th>Name</th><th>Path</th><th>Protocols</th><th>Users</th><th>Mode</th><th></th></tr></thead>
          <tbody>{shares.map((s) => (
            <tr key={s.id}><td><strong>{s.name}</strong></td><td style={{ fontFamily: "monospace", fontSize: 12 }}>{s.path}</td><td>{s.protocols.join(", ")}</td><td>{s.allowed_users.join(", ") || "all"}</td><td>{s.read_only ? "read-only" : "read-write"}</td><td><button className="btn btn-sm btn-danger" onClick={() => remove(s.id)}>Delete</button></td></tr>
          ))}</tbody></table>
      )}
    </div>
  );
}
