import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { providersService } from "@/services/providers.service";

export function useProviders() {
  return useQuery({
    queryKey: ["providers"],
    queryFn: () => providersService.list(),
  });
}

export function useUpdateProviderRouting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, weight }: { id: string; weight: number }) =>
      providersService.updateRouting(id, weight),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });
}

export function useTestProviderConnection() {
  return useMutation({
    mutationFn: (id: string) => providersService.testConnection(id),
  });
}
