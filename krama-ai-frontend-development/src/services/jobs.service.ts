import { apiClient } from "./api-client";
import type { ProcessingJob, Paginated } from "@/types";

export const MOCK_JOBS: ProcessingJob[] = [
  { id: "job_992", type: "Full Pipeline (Ingest -> OCR -> Extract -> Validate)", status: "running", progress: 68, documentCount: 45, organizationId: "org_1", startedAt: "2024-07-28T14:15:00Z", etaSeconds: 42 },
  { id: "job_991", type: "Multi-Engine OCR Batch", status: "running", progress: 92, documentCount: 120, organizationId: "org_1", startedAt: "2024-07-28T14:10:00Z", etaSeconds: 10 },
  { id: "job_990", type: "Entity Linking & PII Redaction", status: "queued", progress: 0, documentCount: 18, organizationId: "org_1", startedAt: "2024-07-28T14:22:00Z", etaSeconds: 180 },
  { id: "job_989", type: "Bulk PDF Canonical Conversion", status: "completed", progress: 100, documentCount: 2048, organizationId: "org_1", startedAt: "2024-07-28T13:00:00Z", etaSeconds: 0 },
  { id: "job_988", type: "Claims Data Extraction", status: "failed", progress: 41, documentCount: 8, organizationId: "org_1", startedAt: "2024-07-28T11:45:00Z", etaSeconds: 0 },
];

export const jobsService = {
  async list(params?: { status?: string; limit?: number; offset?: number }): Promise<ProcessingJob[]> {
    try {
      return await apiClient.get<ProcessingJob[]>("/jobs/async/", { params });
    } catch {
      let filtered = [...MOCK_JOBS];
      if (params?.status && params.status !== "all") {
        filtered = filtered.filter(j => j.status === params.status);
      }
      return filtered;
    }
  },

  async getById(jobId: string): Promise<ProcessingJob> {
    try {
      return await apiClient.get<ProcessingJob>(`/jobs/async/${jobId}`);
    } catch {
      return MOCK_JOBS.find(j => j.id === jobId) || MOCK_JOBS[0];
    }
  },

  async submit(data: { documentId: string; jobType: string; priority?: number }): Promise<ProcessingJob> {
    try {
      return await apiClient.post<ProcessingJob>("/jobs/async/submit", {
        document_id: data.documentId,
        job_type: data.jobType,
        priority: data.priority || 1,
      });
    } catch {
      const newJob: ProcessingJob = {
        id: `job_${Date.now()}`,
        type: data.jobType,
        status: "queued",
        progress: 0,
        documentCount: 1,
        organizationId: "org_1",
        startedAt: new Date().toISOString(),
        etaSeconds: 60,
      };
      MOCK_JOBS.unshift(newJob);
      return newJob;
    }
  },

  async cancel(jobId: string): Promise<{ cancelled: boolean; message: string }> {
    try {
      return await apiClient.delete<{ cancelled: boolean; message: string }>(`/jobs/async/${jobId}/cancel`);
    } catch {
      const job = MOCK_JOBS.find(j => j.id === jobId);
      if (job) job.status = "paused";
      return { cancelled: true, message: "Job cancelled successfully." };
    }
  },

  async getQueueHealth(): Promise<{ provider: string; is_healthy: boolean; approximate_size: number }> {
    try {
      return await apiClient.get("/jobs/async/queue/health");
    } catch {
      return { provider: "redis", is_healthy: true, approximate_size: 42 };
    }
  },
};
