export interface Job {
  id: string;
  type: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  output_file: string | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "offline";
  uptime_seconds: number;
}

export interface Pipeline {
  id: string;
  name: string;
  steps: { operation: string; parameters: Record<string, unknown> }[];
}
