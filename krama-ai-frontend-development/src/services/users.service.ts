import { apiClient } from "./api-client";
import type { UserAccount, UserRole, UserStatus, Paginated, RbacPermission } from "@/types";

export const MOCK_USERS: UserAccount[] = [
  { id: "u1", name: "Krama Admin", email: "admin@krama.ai", role: "owner", status: "active", organizationId: "org_1", organizationName: "Star Health Insurance", mfaEnabled: true, lastActiveAt: "2 mins ago", createdAt: "2024-01-15T08:30:00Z" },
  { id: "u2", name: "Dr. Vikram Sethi", email: "vikram.sethi@starhealth.in", role: "admin", status: "active", organizationId: "org_1", organizationName: "Star Health Insurance", mfaEnabled: true, lastActiveAt: "1 hour ago", createdAt: "2024-02-01T10:15:00Z" },
  { id: "u3", name: "Ananya Sharma", email: "a.sharma@icicilombard.com", role: "reviewer", status: "active", organizationId: "org_2", organizationName: "ICICI Lombard Claims", mfaEnabled: false, lastActiveAt: "Yesterday", createdAt: "2024-03-12T11:00:00Z" },
  { id: "u4", name: "Rajesh Nair", email: "rnair@hdfcergo.com", role: "analyst", status: "invited", organizationId: "org_3", organizationName: "HDFC ERGO General", mfaEnabled: false, lastActiveAt: "—", createdAt: "2024-07-20T16:00:00Z" },
  { id: "u5", name: "Priya Menon", email: "priyam@bajajallianz.com", role: "reviewer", status: "suspended", organizationId: "org_4", organizationName: "Bajaj Allianz TPA", mfaEnabled: true, lastActiveAt: "3 weeks ago", createdAt: "2024-04-05T09:30:00Z" },
  { id: "u6", name: "Siddharth Rao", email: "siddharth.rao@starhealth.in", role: "analyst", status: "active", organizationId: "org_1", organizationName: "Star Health Insurance", mfaEnabled: true, lastActiveAt: "4 hours ago", createdAt: "2024-05-19T14:20:00Z" },
];

export const MOCK_RBAC_PERMISSIONS: RbacPermission[] = [
  { id: "p1", category: "Documents", name: "View Documents", description: "Read-only access to extracted document fields", owner: true, admin: true, reviewer: true, analyst: true },
  { id: "p2", category: "Documents", name: "Upload & Ingest", description: "Upload raw PDFs/images into pipeline", owner: true, admin: true, reviewer: true, analyst: false },
  { id: "p3", category: "Documents", name: "Delete & Purge", description: "Permanently delete documents and extractions", owner: true, admin: true, reviewer: false, analyst: false },
  { id: "p4", category: "Human Review", name: "Approve / Reject", description: "Perform human verification and edit bounding boxes", owner: true, admin: true, reviewer: true, analyst: false },
  { id: "p5", category: "Administration", name: "Invite & Manage Users", description: "Invite new team members and assign roles", owner: true, admin: true, reviewer: false, analyst: false },
  { id: "p6", category: "Administration", name: "Manage AI Providers", description: "Configure API keys, model routing, and fallback threshold", owner: true, admin: true, reviewer: false, analyst: false },
  { id: "p7", category: "Security & Billing", name: "View Audit Logs", description: "Inspect system security events and user activity", owner: true, admin: true, reviewer: false, analyst: false },
  { id: "p8", category: "Security & Billing", name: "Manage Billing & Plan", description: "Update credit card, subscription tier, and quotas", owner: true, admin: false, reviewer: false, analyst: false },
];

export const usersService = {
  async list(params?: { search?: string; role?: string; status?: string }): Promise<Paginated<UserAccount>> {
    try {
      return await apiClient.get<Paginated<UserAccount>>("/users", { params });
    } catch {
      let filtered = [...MOCK_USERS];
      if (params?.search) {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(u => u.name.toLowerCase().includes(s) || u.email.toLowerCase().includes(s));
      }
      if (params?.role && params.role !== "all") {
        filtered = filtered.filter(u => u.role.toLowerCase() === params.role?.toLowerCase());
      }
      if (params?.status && params.status !== "all") {
        filtered = filtered.filter(u => u.status === params.status);
      }
      return {
        items: filtered,
        total: filtered.length,
        page: 1,
        pageSize: 50,
      };
    }
  },

  async invite(data: { email: string; role: UserRole; name?: string; organizationId?: string }): Promise<UserAccount> {
    try {
      return await apiClient.post<UserAccount>("/users/invite", data);
    } catch {
      const newUser: UserAccount = {
        id: `u_${Date.now()}`,
        name: data.name || data.email.split("@")[0],
        email: data.email,
        role: data.role,
        status: "invited",
        organizationId: data.organizationId || "org_1",
        organizationName: "Acme Corporation",
        mfaEnabled: false,
        lastActiveAt: "—",
        createdAt: new Date().toISOString(),
      };
      MOCK_USERS.unshift(newUser);
      return newUser;
    }
  },

  async updateRole(userId: string, role: UserRole): Promise<UserAccount> {
    try {
      return await apiClient.patch<UserAccount>(`/users/${userId}/role`, { role });
    } catch {
      const user = MOCK_USERS.find(u => u.id === userId);
      if (user) {
        user.role = role;
        return user;
      }
      throw new Error("User not found");
    }
  },

  async updateStatus(userId: string, status: UserStatus): Promise<UserAccount> {
    try {
      return await apiClient.patch<UserAccount>(`/users/${userId}/status`, { status });
    } catch {
      const user = MOCK_USERS.find(u => u.id === userId);
      if (user) {
        user.status = status;
        return user;
      }
      throw new Error("User not found");
    }
  },

  async getPermissions(): Promise<RbacPermission[]> {
    try {
      return await apiClient.get<RbacPermission[]>("/users/rbac/permissions");
    } catch {
      return MOCK_RBAC_PERMISSIONS;
    }
  },
};
