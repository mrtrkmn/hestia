import { useState, useEffect, useCallback } from "react";
import api from "../api/client";
import type { Job } from "../types";

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);

  const refresh = useCallback(() => {
    api.get("/jobs").then((r) => setJobs(r.data.jobs ?? [])).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  return { jobs, refresh };
}
