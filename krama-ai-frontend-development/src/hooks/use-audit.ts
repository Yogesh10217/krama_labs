import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { auditService } from "@/services/audit.service";

export function useAuditLogs(params?: { search?: string; category?: string }) {
  return useQuery({
    queryKey: ["audit-logs", params],
    queryFn: () => auditService.listLogs(params),
  });
}

export function useFeatureFlags() {
  return useQuery({
    queryKey: ["feature-flags"],
    queryFn: () => auditService.listFeatureFlags(),
  });
}

export function useToggleFeatureFlag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ key, enabled }: { key: string; enabled: boolean }) =>
      auditService.toggleFeatureFlag(key, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["feature-flags"] });
    },
  });
}
