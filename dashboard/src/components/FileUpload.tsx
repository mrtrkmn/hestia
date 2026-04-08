import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import api from "../api/client";

interface Props {
  onJobCreated?: (jobId: string) => void;
}

export default function FileUpload({ onJobCreated }: Props) {
  const onDrop = useCallback(
    async (files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      try {
        const r = await api.post("/files/upload", form);
        if (onJobCreated) onJobCreated(r.data.file_ids?.[0] ?? "");
      } catch {
        /* handled by interceptor */
      }
    },
    [onJobCreated]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div
      {...getRootProps()}
      style={{
        border: "2px dashed #666",
        borderRadius: 8,
        padding: 40,
        textAlign: "center",
        cursor: "pointer",
      }}
    >
      <input {...getInputProps()} />
      {isDragActive ? <p>Drop files here…</p> : <p>Drag & drop files, or click to select</p>}
    </div>
  );
}
