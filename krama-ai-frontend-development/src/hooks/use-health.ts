import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { healthService } from "@/services/health.service";

export function useSystemHealth() {
  return useQuery({
    queryKey: ["system-health"],
    queryFn: () => healthService.getSystemHealth(),
    refetchInterval: 10000, // Poll every 10 seconds for real-time live monitoring
  });
}

export function useTriggerHealthCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => healthService.triggerHealthCheck(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-health"] });
    },
  });
}
