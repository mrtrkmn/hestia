import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { Automation } from "../types";

export default function IoTPage() {
  const { t } = useTranslation();
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [name, setName] = useState(""); const [triggerType, setTriggerType] = useState<"mqtt"|"cron">("mqtt"); const [mqttTopic, setMqttTopic] = useState(""); const [cronExpr, setCronExpr] = useState("");

  const load = () => api.get("/iot/automations").then((r) => setAutomations(r.data.automations ?? [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const create = async () => { if (!name.trim()) return; await api.post("/iot/automations", { name, trigger_type: triggerType, mqtt_topic: triggerType === "mqtt" ? mqttTopic : undefined, cron_expression: triggerType === "cron" ? cronExpr : undefined, actions: [], enabled: true }); setName(""); setMqttTopic(""); setCronExpr(""); load(); };
  const remove = async (id: string) => { await api.delete(`/iot/automations/${id}`); load(); };

  return (
    <div className="page">
      <h1>{t("iot.title")}</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>{t("iot.create")}</h2>
        <div className="form-row">
          <div className="form-group"><label>{t("iot.name")}</label><input value={name} onChange={(e) => setName(e.target.value)} /></div>
          <div className="form-group"><label>{t("iot.trigger")}</label>
            <select value={triggerType} onChange={(e) => setTriggerType(e.target.value as "mqtt"|"cron")}><option value="mqtt">MQTT</option><option value="cron">Cron</option></select>
          </div>
        </div>
        {triggerType === "mqtt" ? <div className="form-group"><label>{t("iot.mqttTopic")}</label><input value={mqttTopic} onChange={(e) => setMqttTopic(e.target.value)} /></div>
          : <div className="form-group"><label>{t("iot.cronExpression")}</label><input value={cronExpr} onChange={(e) => setCronExpr(e.target.value)} /></div>}
        <button className="btn btn-primary" onClick={create}>{t("iot.createBtn")}</button>
      </div>
      <h2>{t("iot.automations")}</h2>
      {automations.length === 0 ? <div className="empty">{t("iot.noAutomations")}</div> : (
        <table><thead><tr><th>{t("iot.name")}</th><th>{t("iot.trigger")}</th><th>Pattern</th><th>{t("iot.enabled")}</th><th></th></tr></thead>
          <tbody>{automations.map((a) => (
            <tr key={a.id}><td><strong>{a.name}</strong></td><td>{a.trigger_type}</td><td style={{ fontFamily: "monospace", fontSize: 12 }}>{a.mqtt_topic || a.cron_expression}</td><td>{a.enabled ? "✓" : "✗"}</td><td><button className="btn btn-sm btn-danger" onClick={() => remove(a.id)}>{t("iot.delete")}</button></td></tr>
          ))}</tbody></table>
      )}
    </div>
  );
}
