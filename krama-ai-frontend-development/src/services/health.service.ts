import { apiClient } from "./api-client";
import type { SystemServiceHealth } from "@/types";

export const MOCK_SYSTEM_HEALTH: SystemServiceHealth[] = [
  {
    name: "Redis Cache & Queue Store",
    type: "redis",
    status: "healthy",
    uptimePct: 99.99,
    latencyMs: 1.2,
    metrics: {
      memoryPct: 42,
      connections: 128,
      cacheHitRatioPct: 98.4,
    },
    details: "Cluster online (3 primary, 3 replica). Eviction strategy volatile-lru active.",
  },
  {
    name: "PostgreSQL Primary DB",
    type: "postgres",
    status: "healthy",
    uptimePct: 99.98,
    latencyMs: 4.8,
    metrics: {
      cpuPct: 24,
      memoryPct: 58,
      connections: 64,
      storageUsedPct: 62,
    },
    details: "pgvector extension enabled. Write IOPS 1,420/s. Replica lag 4ms.",
  },
  {
    name: "Celery / Redis Job Queue",
    type: "queue",
    status: "healthy",
    uptimePct: 99.95,
    latencyMs: 12,
    metrics: {
      activeQueueCount: 42,
      failedJobsCount: 3,
    },
    details: "High-priority queue latency < 200ms. Dead-letter queue contains 3 items.",
  },
  {
    name: "OCR & Claims Worker Pool",
    type: "worker",
    status: "degraded",
    uptimePct: 98.50,
    latencyMs: 850,
    metrics: {
      cpuPct: 88,
      memoryPct: 91,
      connections: 32,
    },
    details: "Worker pool #4 experienced memory pressure on batch discharge summary parsing. Auto-scaling 2 additional instances.",
  },
  {
    name: "FastAPI Gateway Core",
    type: "api",
    status: "healthy",
    uptimePct: 99.99,
    latencyMs: 28,
    metrics: {
      cpuPct: 18,
      memoryPct: 35,
    },
    details: "Rate limiting active (1,000 req/min/IP). 0 5xx errors in last 24h.",
  },
  {
    name: "S3 / Blob Storage Tier",
    type: "storage",
    status: "healthy",
    uptimePct: 100.0,
    latencyMs: 65,
    metrics: {
      storageUsedPct: 68,
    },
    details: "Cross-region replication enabled (us-east-1 -> us-west-2). Encrypted at rest (KMS).",
  },
];

export const healthService = {
  async getSystemHealth(): Promise<SystemServiceHealth[]> {
    try {
      return await apiClient.get<SystemServiceHealth[]>("/health/system");
    } catch {
      return MOCK_SYSTEM_HEALTH;
    }
  },

  async triggerHealthCheck(): Promise<{ timestamp: string; status: "all_healthy" | "degraded" }> {
    try {
      return await apiClient.post<{ timestamp: string; status: "all_healthy" | "degraded" }>("/health/check");
    } catch {
      return { timestamp: new Date().toISOString(), status: "degraded" };
    }
  },
};
