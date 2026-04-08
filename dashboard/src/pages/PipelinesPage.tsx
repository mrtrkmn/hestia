import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { Pipeline, PipelineStep } from "../types";

const OPS = ["pdf_merge","pdf_split","pdf_ocr","pdf_compress","pdf_to_png","pdf_to_jpeg","images_to_pdf","png_to_jpeg","jpeg_to_png","video_transcode","audio_transcode"];

export default function PipelinesPage() {
  const { t } = useTranslation();
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [name, setName] = useState("");
  const [steps, setSteps] = useState<PipelineStep[]>([{ operation: "pdf_ocr", parameters: {} }]);

  const load = () => api.get("/pipelines").then((r) => setPipelines(r.data.pipelines ?? [])).catch(() => {});
  useEffect(() => { load(); }, []);

  const addStep = () => setSteps([...steps, { operation: "pdf_compress", parameters: {} }]);
  const removeStep = (i: number) => setSteps(steps.filter((_, idx) => idx !== i));
  const updateStep = (i: number, op: string) => { const s = [...steps]; s[i] = { ...s[i], operation: op }; setSteps(s); };

  const create = async () => { if (!name.trim()) return; await api.post("/pipelines", { name, steps, file_ids: [] }); setName(""); setSteps([{ operation: "pdf_ocr", parameters: {} }]); load(); };
  const remove = async (id: string) => { await api.delete(`/pipelines/${id}`); load(); };

  return (
    <div className="page">
      <h1>{t("pipelines.title")}</h1>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>{t("pipelines.create")}</h2>
        <div className="form-group"><label>{t("pipelines.name")}</label><input value={name} onChange={(e) => setName(e.target.value)} /></div>
        {steps.map((s, i) => (
          <div key={i} className="form-row" style={{ alignItems: "end", marginBottom: 8 }}>
            <div className="form-group"><label>{t("pipelines.step", { n: i + 1 })}</label>
              <select value={s.operation} onChange={(e) => updateStep(i, e.target.value)}>{OPS.map((op) => <option key={op} value={op}>{op.replace(/_/g, " ")}</option>)}</select>
            </div>
            {steps.length > 1 && <button className="btn btn-sm btn-danger" onClick={() => removeStep(i)}>✕</button>}
          </div>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button className="btn btn-primary" onClick={addStep}>{t("pipelines.addStep")}</button>
          <button className="btn btn-primary" onClick={create}>{t("pipelines.save")}</button>
        </div>
      </div>
      <h2>{t("pipelines.saved")}</h2>
      {pipelines.length === 0 ? <div className="empty">{t("pipelines.noPipelines")}</div> : (
        <table><thead><tr><th>{t("pipelines.name")}</th><th>Steps</th><th></th></tr></thead>
          <tbody>{pipelines.map((p) => (
            <tr key={p.id}><td><strong>{p.name}</strong></td><td>{p.steps.map((s) => s.operation.replace(/_/g, " ")).join(" → ")}</td><td><button className="btn btn-sm btn-danger" onClick={() => remove(p.id)}>{t("pipelines.delete")}</button></td></tr>
          ))}</tbody></table>
      )}
    </div>
  );
}
