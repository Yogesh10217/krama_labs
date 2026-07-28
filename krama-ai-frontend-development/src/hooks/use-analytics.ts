import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics.service";

export function useSystemAnalytics(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ["analytics-system", startDate, endDate],
    queryFn: () => analyticsService.getSystemOverview(startDate, endDate),
  });
}

export function useProviderAnalytics(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ["analytics-providers", startDate, endDate],
    queryFn: () => analyticsService.getProviderOverview(startDate, endDate),
  });
}

export function useOrgAnalytics(orgId: string, startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ["analytics-org", orgId, startDate, endDate],
    queryFn: () => analyticsService.getOrganizationOverview(orgId, startDate, endDate),
    enabled: Boolean(orgId),
  });
}
