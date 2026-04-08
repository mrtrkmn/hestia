import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { StorageShare } from "../types";

export default function StoragePage() {
  const { t } = useTranslation();
  const [shares, setShares] = useState<StorageShare[]>([]);
  const [name, setName] = useState(""); const [path, setPath] = useState("/srv/storage/"); const [users, setUsers] = useState(""); const [readOnly, setReadOnly] = useState(false);

  const load = () => api.get("/storage/shares").then((r) => setShares(r.data.shares ?? [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const create = async () => { if (!name.trim()) return; await api.post("/storage/shares", { name, path, protocols: ["smb"], allowed_users: users.split(",").map((u) => u.trim()).filter(Boolean), read_only: readOnly }); setName(""); setPath("/srv/storage/"); setUsers(""); setReadOnly(false); load(); };
  const remove = async (id: string) => { await api.delete(`/storage/shares/${id}`); load(); };

  return (
    <div className="page">
      <h1>{t("storage.title")}</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>{t("storage.createShare")}</h2>
        <div className="form-row">
          <div className="form-group"><label>{t("storage.shareName")}</label><input value={name} onChange={(e) => setName(e.target.value)} /></div>
          <div className="form-group"><label>{t("storage.path")}</label><input value={path} onChange={(e) => setPath(e.target.value)} /></div>
        </div>
        <div className="form-row">
          <div className="form-group"><label>{t("storage.allowedUsers")}</label><input value={users} onChange={(e) => setUsers(e.target.value)} /></div>
          <div className="form-group"><label>{t("storage.readOnly")}</label><label className="toggle" style={{ marginTop: 4 }}><input type="checkbox" checked={readOnly} onChange={(e) => setReadOnly(e.target.checked)} /><span className="slider" /></label></div>
        </div>
        <button className="btn btn-primary" onClick={create}>{t("storage.create")}</button>
      </div>
      <h2>{t("storage.shares")}</h2>
      {shares.length === 0 ? <div className="empty">{t("storage.noShares")}</div> : (
        <table><thead><tr><th>{t("storage.shareName")}</th><th>{t("storage.path")}</th><th>{t("storage.protocols")}</th><th>{t("storage.users")}</th><th>{t("storage.mode")}</th><th></th></tr></thead>
          <tbody>{shares.map((s) => (
            <tr key={s.id}><td><strong>{s.name}</strong></td><td style={{ fontFamily: "monospace", fontSize: 12 }}>{s.path}</td><td>{s.protocols.join(", ")}</td><td>{s.allowed_users.join(", ") || t("storage.all")}</td><td>{s.read_only ? t("storage.readOnlyLabel") : t("storage.readWrite")}</td><td><button className="btn btn-sm btn-danger" onClick={() => remove(s.id)}>{t("storage.delete")}</button></td></tr>
          ))}</tbody></table>
      )}
    </div>
  );
}
