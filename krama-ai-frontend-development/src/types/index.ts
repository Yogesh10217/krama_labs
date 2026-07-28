/**
 * Shared domain types mirroring the FastAPI backend contracts.
 * Keep these in sync with the backend Pydantic schemas.
 */

export type { SessionUser } from "./navigation";

export type DocumentStatus = "uploaded" | "processing" | "extracted" | "review" | "failed";
export type JobStatus = "queued" | "running" | "paused" | "completed" | "failed";
export type ReviewDecision = "approved" | "rejected" | "changes_requested";
export type UserRole = "owner" | "admin" | "reviewer" | "analyst";
export type UserStatus = "active" | "invited" | "suspended";
export type ProviderStatus = "operational" | "degraded" | "offline";

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface DocumentSummary {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
  status: DocumentStatus;
  organizationId: string;
  createdAt: string;
}

export interface ExtractedField {
  key: string;
  value: string;
  confidence: number;
  needsReview: boolean;
  boundingBox?: { page: number; x: number; y: number; width: number; height: number };
}

export interface DocumentDetail extends DocumentSummary {
  fields: ExtractedField[];
  metadata: Record<string, string>;
  timeline: Array<{ timestamp: string; event: string; level: "info" | "warning" | "error" }>;
}

export interface ProcessingJob {
  id: string;
  type: string;
  status: JobStatus;
  progress: number;
  documentCount: number;
  organizationId: string;
  startedAt: string;
  etaSeconds?: number;
}

export interface Organization {
  id: string;
  name: string;
  plan: "startup" | "pro" | "enterprise";
  status: "active" | "trial" | "past_due" | "suspended";
  memberCount: number;
  documentCount: number;
  storageUsedBytes: number;
  storageQuotaBytes: number;
  domain: string;
  createdAt: string;
}

export interface UserAccount {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  organizationId: string;
  organizationName?: string;
  avatarUrl?: string;
  mfaEnabled?: boolean;
  lastActiveAt?: string;
  createdAt?: string;
}

export interface Provider {
  id: string;
  name: string;
  type: "openai" | "gemini" | "anthropic" | "ollama" | "custom";
  model: string;
  status: ProviderStatus;
  routingWeight: number;
  p95LatencyMs: number;
  errorRate: number;
  apiKeyConfigured: boolean;
  endpointUrl?: string;
  monthlySpendUsd: number;
}

export interface AuditLog {
  id: string;
  actor: {
    id: string;
    name: string;
    email: string;
  };
  action: string;
  target: string;
  category: "auth" | "document" | "user" | "organization" | "provider" | "security";
  ipAddress: string;
  userAgent?: string;
  timestamp: string;
  status: "success" | "warning" | "error";
  details?: Record<string, unknown>;
}

export interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  category: "ocr" | "ai" | "security" | "review" | "experimental";
  enabled: boolean;
  rolloutPercentage: number;
  updatedAt: string;
  updatedBy: string;
}

export interface SystemServiceHealth {
  name: string;
  type: "redis" | "postgres" | "queue" | "worker" | "api" | "storage";
  status: "healthy" | "degraded" | "critical";
  uptimePct: number;
  latencyMs: number;
  metrics: {
    cpuPct?: number;
    memoryPct?: number;
    connections?: number;
    activeQueueCount?: number;
    failedJobsCount?: number;
    cacheHitRatioPct?: number;
    storageUsedPct?: number;
  };
  details: string;
}

export interface ApiKeyItem {
  id: string;
  name: string;
  keyPrefix: string;
  createdAt: string;
  lastUsedAt?: string;
  expiresAt?: string;
  permissions: string[];
  status: "active" | "revoked";
}

export interface SecuritySession {
  id: string;
  device: string;
  browser: string;
  ipAddress: string;
  location: string;
  lastActive: string;
  isCurrent: boolean;
}

export interface RbacPermission {
  id: string;
  category: string;
  name: string;
  description: string;
  owner: boolean;
  admin: boolean;
  reviewer: boolean;
  analyst: boolean;
}

