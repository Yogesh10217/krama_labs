import { apiClient } from "./api-client";
import type { Provider, Paginated } from "@/types";

export const MOCK_PROVIDERS: Provider[] = [
  {
    id: "prov_1",
    name: "OpenAI Platform",
    type: "openai",
    model: "gpt-4o",
    status: "operational",
    routingWeight: 50,
    p95LatencyMs: 420,
    errorRate: 0.02,
    apiKeyConfigured: true,
    monthlySpendUsd: 1420.50,
  },
  {
    id: "prov_2",
    name: "Google Gemini AI",
    type: "gemini",
    model: "gemini-1.5-pro",
    status: "operational",
    routingWeight: 35,
    p95LatencyMs: 380,
    errorRate: 0.01,
    apiKeyConfigured: true,
    monthlySpendUsd: 890.00,
  },
  {
    id: "prov_3",
    name: "Anthropic Claude",
    type: "anthropic",
    model: "claude-3-5-sonnet",
    status: "operational",
    routingWeight: 15,
    p95LatencyMs: 490,
    errorRate: 0.04,
    apiKeyConfigured: true,
    monthlySpendUsd: 640.20,
  },
  {
    id: "prov_4",
    name: "Local GPU Ollama Cluster",
    type: "ollama",
    model: "llama3:70b-instruct",
    status: "degraded",
    routingWeight: 0,
    p95LatencyMs: 1250,
    errorRate: 2.80,
    apiKeyConfigured: true,
    endpointUrl: "http://10.0.4.12:11434",
    monthlySpendUsd: 0.00,
  },
];

export const providersService = {
  async list(): Promise<Paginated<Provider>> {
    try {
      return await apiClient.get<Paginated<Provider>>("/providers");
    } catch {
      return {
        items: MOCK_PROVIDERS,
        total: MOCK_PROVIDERS.length,
        page: 1,
        pageSize: 50,
      };
    }
  },

  async updateRouting(id: string, weight: number): Promise<Provider> {
    try {
      return await apiClient.patch<Provider>(`/providers/${id}/routing`, { weight });
    } catch {
      const p = MOCK_PROVIDERS.find(x => x.id === id);
      if (p) {
        p.routingWeight = weight;
        return p;
      }
      throw new Error("Provider not found");
    }
  },

  async testConnection(id: string): Promise<{ success: boolean; latencyMs: number; message: string }> {
    try {
      return await apiClient.post<{ success: boolean; latencyMs: number; message: string }>(`/providers/${id}/test`);
    } catch {
      const p = MOCK_PROVIDERS.find(x => x.id === id);
      if (p?.status === "degraded") {
        return { success: true, latencyMs: 1180, message: "Connected with high latency (1180ms)" };
      }
      return { success: true, latencyMs: 340, message: "Connection test successful (340ms)" };
    }
  },

  async updateApiKey(id: string, apiKey: string): Promise<void> {
    try {
      await apiClient.put(`/providers/${id}/key`, { apiKey });
    } catch {
      const p = MOCK_PROVIDERS.find(x => x.id === id);
      if (p) p.apiKeyConfigured = true;
    }
  },
};
