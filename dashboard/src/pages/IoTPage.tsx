import { useState, useEffect } from "react";
import api from "../api/client";
import type { Automation } from "../types";

export default function IoTPage() {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [name, setName] = useState("");
  const [triggerType, setTriggerType] = useState<"mqtt" | "cron">("mqtt");
  const [mqttTopic, setMqttTopic] = useState("");
  const [cronExpr, setCronExpr] = useState("");

  const load = () => api.get("/iot/automations").then((r) => setAutomations(r.data.automations ?? [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    await api.post("/iot/automations", {
      name, trigger_type: triggerType,
      mqtt_topic: triggerType === "mqtt" ? mqttTopic : undefined,
      cron_expression: triggerType === "cron" ? cronExpr : undefined,
      actions: [], enabled: true,
    });
    setName(""); setMqttTopic(""); setCronExpr("");
    load();
  };

  const remove = async (id: string) => { await api.delete(`/iot/automations/${id}`); load(); };

  return (
    <div className="page">
      <h1>IoT & Automations</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Create Automation</h2>
        <div className="form-row">
          <div className="form-group"><label>Name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="heat-alert" /></div>
          <div className="form-group"><label>Trigger</label>
            <select value={triggerType} onChange={(e) => setTriggerType(e.target.value as "mqtt" | "cron")}>
              <option value="mqtt">MQTT topic</option><option value="cron">Cron schedule</option>
            </select>
          </div>
        </div>
        {triggerType === "mqtt" ? (
          <div className="form-group"><label>MQTT topic pattern</label><input value={mqttTopic} onChange={(e) => setMqttTopic(e.target.value)} placeholder="home/+/temperature" /></div>
        ) : (
          <div className="form-group"><label>Cron expression</label><input value={cronExpr} onChange={(e) => setCronExpr(e.target.value)} placeholder="0 2 * * *" /></div>
        )}
        <button className="btn btn-primary" onClick={create}>Create automation</button>
      </div>
      <h2>Automations</h2>
      {automations.length === 0 ? <div className="empty">No automations configured.</div> : (
        <table><thead><tr><th>Name</th><th>Trigger</th><th>Pattern</th><th>Enabled</th><th></th></tr></thead>
          <tbody>{automations.map((a) => (
            <tr key={a.id}><td><strong>{a.name}</strong></td><td>{a.trigger_type}</td><td style={{ fontFamily: "monospace", fontSize: 12 }}>{a.mqtt_topic || a.cron_expression}</td><td>{a.enabled ? "✓" : "✗"}</td><td><button className="btn btn-sm btn-danger" onClick={() => remove(a.id)}>Delete</button></td></tr>
          ))}</tbody></table>
      )}
    </div>
  );
}
