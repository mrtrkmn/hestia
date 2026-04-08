import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useDropzone } from "react-dropzone";
import { useJobs } from "../hooks/useJobs";
import api from "../api/client";

export default function FilesPage() {
  const { t } = useTranslation();
  const { jobs, refresh } = useJobs();
  const [operation, setOperation] = useState("pdf_merge");
  const [targetFormat, setTargetFormat] = useState("pdf");
  const [fileIds, setFileIds] = useState<string[]>([]);

  const onDrop = useCallback(async (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    try { const r = await api.post("/files/upload", form); setFileIds(r.data.file_ids ?? []); } catch {}
  }, []);

  const submit = async () => {
    if (fileIds.length === 0) return;
    try { await api.post("/files/process", { operation, source_format: "pdf", target_format: targetFormat, file_ids: fileIds }); refresh(); setFileIds([]); } catch {}
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div className="page">
      <h1>{t("files.title")}</h1>
      <div className={`dropzone ${isDragActive ? "active" : ""}`} {...getRootProps()}>
        <input {...getInputProps()} />
        {fileIds.length > 0 ? <p>{t("files.filesUploaded", { count: fileIds.length })}</p> : <p>{t("files.dropzone")}</p>}
      </div>
      {fileIds.length > 0 && (
        <div className="card" style={{ marginTop: 12 }}>
          <div className="form-row">
            <div className="form-group"><label>{t("files.operation")}</label>
              <select value={operation} onChange={(e) => setOperation(e.target.value)}>
                <optgroup label="PDF"><option value="pdf_merge">Merge</option><option value="pdf_split">Split</option><option value="pdf_ocr">OCR</option><option value="pdf_compress">Compress</option></optgroup>
                <optgroup label="Image"><option value="pdf_to_png">PDF → PNG</option><option value="pdf_to_jpeg">PDF → JPEG</option><option value="images_to_pdf">Images → PDF</option><option value="png_to_jpeg">PNG → JPEG</option><option value="jpeg_to_png">JPEG → PNG</option></optgroup>
                <optgroup label="Media"><option value="video_transcode">Video</option><option value="audio_transcode">Audio</option></optgroup>
              </select>
            </div>
            <div className="form-group"><label>{t("files.targetFormat")}</label>
              <select value={targetFormat} onChange={(e) => setTargetFormat(e.target.value)}>
                <option value="pdf">PDF</option><option value="png">PNG</option><option value="jpeg">JPEG</option><option value="mp4">MP4</option><option value="mp3">MP3</option><option value="ogg">OGG</option>
              </select>
            </div>
          </div>
          <button className="btn btn-primary" onClick={submit}>{t("files.process")}</button>
        </div>
      )}
      <h2>{t("files.jobs")}</h2>
      {jobs.length === 0 ? <div className="empty">{t("files.noJobs")}</div> : (
        <table><thead><tr><th>ID</th><th>{t("files.operation")}</th><th>Status</th><th>Progress</th><th></th></tr></thead>
          <tbody>{jobs.map((j) => (
            <tr key={j.id}><td style={{ fontFamily: "monospace", fontSize: 12 }}>{j.id.slice(0, 8)}</td><td>{j.type}</td><td><span className={`badge badge-${j.status}`}>{j.status}</span></td>
              <td><div className="progress-bar" style={{ width: 100 }}><div className="progress-bar-fill" style={{ width: `${j.progress}%` }} /></div></td>
              <td>{j.status === "completed" && j.output_file && <a href={`/api/v1/files/${j.output_file}/download`} className="btn btn-sm btn-primary">{t("files.download")}</a>}
                {j.status === "pending" && <button className="btn btn-sm btn-danger" onClick={async () => { await api.delete(`/jobs/${j.id}`); refresh(); }}>{t("files.cancel")}</button>}</td></tr>
          ))}</tbody></table>
      )}
    </div>
  );
}
