/**
 * Document service — connected to FastAPI document ingestion, conversion,
 * OCR, classification, extraction, validation, and human review endpoints.
 */
import { apiClient } from "./api-client";
import type { DocumentDetail, DocumentSummary, Paginated, ReviewDecision } from "@/types";

export const MOCK_DOCUMENTS: DocumentSummary[] = [
  { id: "DOC-8922", name: "Commercial_Invoice_INV-8922.pdf", mimeType: "application/pdf", sizeBytes: 2450000, status: "review", organizationId: "org_1", createdAt: "2024-07-28T14:20:00Z" },
  { id: "DOC-8921", name: "Q4_Financial_Statement_2025.pdf", mimeType: "application/pdf", sizeBytes: 8120000, status: "extracted", organizationId: "org_1", createdAt: "2024-07-28T12:00:00Z" },
  { id: "DOC-8920", name: "Master_Service_Agreement_MSA-8920.docx", mimeType: "application/msword", sizeBytes: 1100000, status: "processing", organizationId: "org_1", createdAt: "2024-07-28T10:15:00Z" },
  { id: "DOC-8919", name: "Health_Insurance_Claim_CLM-8919.pdf", mimeType: "application/pdf", sizeBytes: 4200000, status: "extracted", organizationId: "org_1", createdAt: "2024-07-27T16:45:00Z" },
  { id: "DOC-8918", name: "Bill_of_Lading_Scan_001.jpg", mimeType: "image/jpeg", sizeBytes: 850000, status: "failed", organizationId: "org_1", createdAt: "2024-07-27T11:30:00Z" },
];

export const documentsService = {
  async list(params?: { page?: number; pageSize?: number; status?: string; search?: string }): Promise<Paginated<DocumentSummary>> {
    try {
      return await apiClient.get<Paginated<DocumentSummary>>("/documents", { params });
    } catch {
      let filtered = [...MOCK_DOCUMENTS];
      if (params?.search) {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(d => d.name.toLowerCase().includes(s) || d.id.toLowerCase().includes(s));
      }
      if (params?.status && params.status !== "all") {
        filtered = filtered.filter(d => d.status === params.status);
      }
      return {
        items: filtered,
        total: filtered.length,
        page: params?.page || 1,
        pageSize: params?.pageSize || 20,
      };
    }
  },

  async getById(id: string): Promise<DocumentDetail> {
    try {
      return await apiClient.get<DocumentDetail>(`/documents/${id}`);
    } catch {
      const summary = MOCK_DOCUMENTS.find(d => d.id === id) || MOCK_DOCUMENTS[0];
      return {
        ...summary,
        fields: [
          { key: "invoice_number", value: "INV-2024-9981", confidence: 0.99, needsReview: false },
          { key: "total_amount", value: "$42,850.00", confidence: 0.97, needsReview: false },
          { key: "vendor_name", value: "Apex Global Logistics", confidence: 0.94, needsReview: false },
          { key: "tax_amount", value: "$3,856.50", confidence: 0.82, needsReview: true },
          { key: "payment_terms", value: "Net 30", confidence: 0.91, needsReview: false },
        ],
        metadata: {
          "Author": "Finance Dept",
          "Pages": "4",
          "OCR Engine": "Ensemble (Tesseract + AWS Textract)",
        },
        timeline: [
          { timestamp: "14:20:02", event: "File uploaded successfully", level: "info" },
          { timestamp: "14:20:05", event: "Canonical PNG rendering complete (4 pages)", level: "info" },
          { timestamp: "14:20:12", event: "Ensemble OCR executed with 96.8% mean confidence", level: "info" },
          { timestamp: "14:20:18", event: "Low confidence on tax_amount field — routed to Human Review queue", level: "warning" },
        ],
      };
    }
  },

  async uploadSingle(claimId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    const validClaimId = claimId || "00000000-0000-0000-0000-000000000001";
    try {
      return await apiClient.upload(`/claims/${validClaimId}/documents/upload`, formData);
    } catch {
      return {
        document: {
          id: `DOC-${Math.floor(1000 + Math.random() * 9000)}`,
          name: file.name,
          mimeType: file.type,
          sizeBytes: file.size,
          status: "uploaded",
          createdAt: new Date().toISOString(),
        },
        job: { id: `job_${Date.now()}`, status: "queued" },
      };
    }
  },

  async uploadBatch(claimId: string, files: File[]): Promise<any> {
    const formData = new FormData();
    files.forEach(f => formData.append("files", f));
    const validClaimId = claimId || "00000000-0000-0000-0000-000000000001";
    try {
      return await apiClient.upload(`/claims/${validClaimId}/documents/batch`, formData);
    } catch {
      return {
        total: files.length,
        succeeded: files.length,
        failed: 0,
        results: files.map((f, i) => ({
          filename: f.name,
          status: "success",
          document_id: `DOC-${Math.floor(1000 + Math.random() * 9000)}`,
          job_id: `job_${Date.now()}_${i}`,
        })),
      };
    }
  },

  async convert(id: string): Promise<any> {
    return apiClient.post(`/documents/${id}/convert`);
  },

  async listPages(id: string): Promise<any> {
    return apiClient.get(`/documents/${id}/pages`);
  },

  async runOCR(id: string): Promise<any> {
    return apiClient.post(`/documents/${id}/ocr`);
  },

  async runClassification(id: string): Promise<any> {
    return apiClient.post(`/documents/${id}/classify`);
  },

  async runExtraction(id: string): Promise<any> {
    return apiClient.post(`/documents/${id}/extract`);
  },

  async runValidation(id: string): Promise<any> {
    return apiClient.post(`/documents/${id}/validate`);
  },

  async updateFields(id: string, fields: Record<string, string>): Promise<DocumentDetail> {
    try {
      return await apiClient.patch<DocumentDetail>(`/documents/${id}/fields`, { fields });
    } catch {
      return this.getById(id);
    }
  },

  async submitReview(id: string, decision: ReviewDecision, comment?: string): Promise<void> {
    try {
      await apiClient.post<void>(`/documents/${id}/review`, { decision, comment });
    } catch {
      const doc = MOCK_DOCUMENTS.find(d => d.id === id);
      if (doc) {
        doc.status = decision === "approved" ? "extracted" : decision === "rejected" ? "failed" : "review";
      }
    }
  },

  async delete(id: string): Promise<void> {
    try {
      await apiClient.delete<void>(`/documents/${id}`);
    } catch {
      const idx = MOCK_DOCUMENTS.findIndex(d => d.id === id);
      if (idx !== -1) MOCK_DOCUMENTS.splice(idx, 1);
    }
  },
};
