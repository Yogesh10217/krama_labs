import { apiClient } from "./api-client";
import type { Organization, Paginated } from "@/types";

export const MOCK_ORGANIZATIONS: Organization[] = [
  {
    id: "org_1",
    name: "Star Health & Allied Insurance",
    plan: "enterprise",
    status: "active",
    memberCount: 148,
    documentCount: 84200,
    storageUsedBytes: 1288490188800, // 1.2 TB
    storageQuotaBytes: 2199023255552, // 2.0 TB
    domain: "starhealth.in",
    createdAt: "2024-01-15T08:30:00Z",
  },
  {
    id: "org_2",
    name: "ICICI Lombard Claims Division",
    plan: "pro",
    status: "active",
    memberCount: 52,
    documentCount: 32800,
    storageUsedBytes: 579820584960, // 540 GB
    storageQuotaBytes: 1099511627776, // 1.0 TB
    domain: "icicilombard.com",
    createdAt: "2024-03-10T14:15:00Z",
  },
  {
    id: "org_3",
    name: "HDFC ERGO General Insurance",
    plan: "startup",
    status: "trial",
    memberCount: 21,
    documentCount: 18100,
    storageUsedBytes: 332859965440, // 310 GB
    storageQuotaBytes: 536870912000, // 500 GB
    domain: "hdfcergo.com",
    createdAt: "2024-06-01T09:00:00Z",
  },
  {
    id: "org_4",
    name: "Bajaj Allianz TPA Services",
    plan: "pro",
    status: "past_due",
    memberCount: 27,
    documentCount: 9400,
    storageUsedBytes: 161061273600, // 150 GB
    storageQuotaBytes: 536870912000, // 500 GB
    domain: "bajajallianz.com",
    createdAt: "2024-05-18T11:45:00Z",
  },
];

export const organizationsService = {
  async list(params?: { search?: string; plan?: string }): Promise<Paginated<Organization>> {
    try {
      return await apiClient.get<Paginated<Organization>>("/organizations", { params });
    } catch {
      let filtered = [...MOCK_ORGANIZATIONS];
      if (params?.search) {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(o => o.name.toLowerCase().includes(s) || o.domain.toLowerCase().includes(s));
      }
      if (params?.plan && params.plan !== "all") {
        filtered = filtered.filter(o => o.plan === params.plan);
      }
      return {
        items: filtered,
        total: filtered.length,
        page: 1,
        pageSize: 50,
      };
    }
  },

  async create(data: Partial<Organization>): Promise<Organization> {
    try {
      return await apiClient.post<Organization>("/organizations", data);
    } catch {
      const newOrg: Organization = {
        id: `org_${Date.now()}`,
        name: data.name || "New Workspace",
        plan: data.plan || "startup",
        status: "active",
        memberCount: 1,
        documentCount: 0,
        storageUsedBytes: 0,
        storageQuotaBytes: 536870912000,
        domain: data.domain || "company.com",
        createdAt: new Date().toISOString(),
      };
      MOCK_ORGANIZATIONS.unshift(newOrg);
      return newOrg;
    }
  },

  async update(id: string, data: Partial<Organization>): Promise<Organization> {
    try {
      return await apiClient.patch<Organization>(`/organizations/${id}`, data);
    } catch {
      const index = MOCK_ORGANIZATIONS.findIndex(o => o.id === id);
      if (index !== -1) {
        MOCK_ORGANIZATIONS[index] = { ...MOCK_ORGANIZATIONS[index], ...data };
        return MOCK_ORGANIZATIONS[index];
      }
      throw new Error("Organization not found");
    }
  },
};
