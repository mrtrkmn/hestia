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
  steps: PipelineStep[];
}

export interface PipelineStep {
  operation: string;
  parameters: Record<string, unknown>;
}

export interface StorageShare {
  id: string;
  name: string;
  path: string;
  protocols: string[];
  allowed_users: string[];
  read_only: boolean;
}

export interface Automation {
  id: string;
  name: string;
  trigger_type: "mqtt" | "cron";
  mqtt_topic?: string;
  cron_expression?: string;
  actions: AutomationAction[];
  enabled: boolean;
}

export interface AutomationAction {
  type: string;
  parameters: Record<string, unknown>;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: "admin" | "user";
  totp_enabled: boolean;
}

export interface LogEntry {
  event_type: string;
  timestamp: string;
  source_ip: string;
  user: string;
  resource: string;
  details: string;
}
