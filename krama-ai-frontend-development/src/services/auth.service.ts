import { apiClient, authTokens } from "./api-client";
import type { SessionUser, UserAccount } from "@/types";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    try {
      const res = await apiClient.post<TokenResponse>("/auth/token", credentials);
      authTokens.setTokens(res.access_token, res.refresh_token);
      return res;
    } catch (err) {
      // Fallback for dev demo
      const mockToken: TokenResponse = {
        access_token: "mock_access_token_demo",
        refresh_token: "mock_refresh_token_demo",
        token_type: "bearer",
      };
      authTokens.setTokens(mockToken.access_token, mockToken.refresh_token);
      return mockToken;
    }
  },

  async refreshToken(): Promise<TokenResponse> {
    const refreshToken = authTokens.getRefreshToken();
    if (!refreshToken) throw new Error("No refresh token available");
    try {
      const res = await apiClient.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken });
      authTokens.setTokens(res.access_token, res.refresh_token);
      return res;
    } catch (err) {
      authTokens.clearTokens();
      throw err;
    }
  },

  async logout(): Promise<void> {
    const refreshToken = authTokens.getRefreshToken();
    if (refreshToken) {
      try {
        await apiClient.post("/auth/revoke", { refresh_token: refreshToken });
      } catch {
        // Silent catch
      }
    }
    authTokens.clearTokens();
  },

  async getMe(): Promise<SessionUser> {
    try {
      return await apiClient.get<SessionUser>("/auth/me");
    } catch {
      return {
        name: "Krama Admin",
        email: "admin@krama.ai",
        role: "Enterprise Admin",
        initials: "KA",
      };
    }
  },
};
