import { apiClient } from "./api-client";
import type { AuditLog, FeatureFlag, Paginated } from "@/types";

export const MOCK_AUDIT_LOGS: AuditLog[] = [
  {
    id: "log_101",
    actor: { id: "u1", name: "Krama Admin", email: "admin@krama.ai" },
    action: "user.role.update",
    target: "vikram.sethi@starhealth.in (Admin -> Owner)",
    category: "security",
    ipAddress: "192.168.1.104",
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    timestamp: "2024-07-28T20:15:30Z",
    status: "success",
    details: { previousRole: "admin", newRole: "owner" },
  },
  {
    id: "log_102",
    actor: { id: "u2", name: "Dr. Vikram Sethi", email: "vikram.sethi@starhealth.in" },
    action: "provider.key.rotate",
    target: "OpenAI Azure Gateway (prov_1)",
    category: "provider",
    ipAddress: "10.0.1.22",
    userAgent: "Krama CLI / v2.4.0",
    timestamp: "2024-07-28T19:40:12Z",
    status: "success",
    details: { providerId: "prov_1" },
  },
  {
    id: "log_103",
    actor: { id: "u3", name: "Ananya Sharma", email: "a.sharma@icicilombard.com" },
    action: "document.human_review.approve",
    target: "DOC-8922 (Discharge_Summary_DS-8922.pdf)",
    category: "document",
    ipAddress: "172.16.4.55",
    timestamp: "2024-07-28T18:12:00Z",
    status: "success",
    details: { confidenceBefore: 0.78, verifiedFieldsCount: 14 },
  },
  {
    id: "log_104",
    actor: { id: "u5", name: "Priya Menon", email: "priyam@bajajallianz.com" },
    action: "auth.login.failed",
    target: "Invalid Password (3 attempts)",
    category: "auth",
    ipAddress: "45.33.12.89",
    timestamp: "2024-07-28T17:05:44Z",
    status: "error",
    details: { lockTriggered: true },
  },
  {
    id: "log_105",
    actor: { id: "u1", name: "Krama Admin", email: "admin@krama.ai" },
    action: "feature_flag.toggle",
    target: "ICD-10 Multi-Engine Medical Consensus (ocr_multi_engine)",
    category: "organization",
    ipAddress: "192.168.1.104",
    timestamp: "2024-07-28T15:22:10Z",
    status: "warning",
    details: { flagKey: "ocr_multi_engine", newValue: true },
  },
];

export const MOCK_FEATURE_FLAGS: FeatureFlag[] = [
  {
    key: "ai_auto_approval",
    name: "AI High-Confidence Auto-Approval",
    description: "Automatically approve documents with mean extraction confidence > 98.5%",
    category: "ai",
    enabled: true,
    rolloutPercentage: 100,
    updatedAt: "2024-07-20T10:00:00Z",
    updatedBy: "Alice Donovan",
  },
  {
    key: "ocr_multi_engine",
    name: "Multi-Engine OCR Consensus",
    description: "Run Tesseract, EasyOCR, and AWS Textract in parallel for ensemble accuracy",
    category: "ocr",
    enabled: true,
    rolloutPercentage: 50,
    updatedAt: "2024-07-25T14:30:00Z",
    updatedBy: "Ben Kessler",
  },
  {
    key: "pii_redaction_strict",
    name: "Strict PII & PHI Auto-Redaction",
    description: "Automatically mask SSNs, credit card numbers, and medical IDs before cloud indexing",
    category: "security",
    enabled: true,
    rolloutPercentage: 100,
    updatedAt: "2024-06-15T08:00:00Z",
    updatedBy: "Alice Donovan",
  },
  {
    key: "human_review_dual_sign",
    name: "Dual-Signoff Human Review",
    description: "Require 2 independent human reviewers for documents > $100,000 value",
    category: "review",
    enabled: false,
    rolloutPercentage: 0,
    updatedAt: "2024-07-10T11:15:00Z",
    updatedBy: "Alice Donovan",
  },
  {
    key: "vector_hybrid_search",
    name: "Hybrid Vector + BM25 Search",
    description: "Combine pgvector dense embeddings with sparse keyword indexing in Document Search",
    category: "experimental",
    enabled: true,
    rolloutPercentage: 25,
    updatedAt: "2024-07-28T09:00:00Z",
    updatedBy: "Ben Kessler",
  },
];

export const auditService = {
  async listLogs(params?: { search?: string; category?: string }): Promise<Paginated<AuditLog>> {
    try {
      return await apiClient.get<Paginated<AuditLog>>("/audit/logs", { params });
    } catch {
      let filtered = [...MOCK_AUDIT_LOGS];
      if (params?.search) {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(
          l => l.action.toLowerCase().includes(s) || l.target.toLowerCase().includes(s) || l.actor.name.toLowerCase().includes(s)
        );
      }
      if (params?.category && params.category !== "all") {
        filtered = filtered.filter(l => l.category === params.category);
      }
      return { items: filtered, total: filtered.length, page: 1, pageSize: 50 };
    }
  },

  async listFeatureFlags(): Promise<FeatureFlag[]> {
    try {
      return await apiClient.get<FeatureFlag[]>("/audit/feature-flags");
    } catch {
      return MOCK_FEATURE_FLAGS;
    }
  },

  async toggleFeatureFlag(key: string, enabled: boolean): Promise<FeatureFlag> {
    try {
      return await apiClient.patch<FeatureFlag>(`/audit/feature-flags/${key}`, { enabled });
    } catch {
      const flag = MOCK_FEATURE_FLAGS.find(f => f.key === key);
      if (flag) {
        flag.enabled = enabled;
        flag.updatedAt = new Date().toISOString();
        return flag;
      }
      throw new Error("Feature flag not found");
    }
  },
};
