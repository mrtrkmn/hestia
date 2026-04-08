import FileUpload from "../components/FileUpload";
import { useJobs } from "../hooks/useJobs";

export default function FilesPage() {
  const { jobs, refresh } = useJobs();

  return (
    <div>
      <h1>File Processing</h1>
      <FileUpload onJobCreated={() => refresh()} />
      <h2>Jobs</h2>
      {jobs.length === 0 ? (
        <p>No jobs yet.</p>
      ) : (
        <ul>
          {jobs.map((j) => (
            <li key={j.id}>
              {j.id} — {j.status} ({j.progress}%)
              {j.status === "completed" && j.output_file && (
                <a href={`/api/v1/files/${j.output_file}/download`}> Download</a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
