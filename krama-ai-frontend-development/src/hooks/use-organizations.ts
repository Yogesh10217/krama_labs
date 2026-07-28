import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { organizationsService } from "@/services/organizations.service";
import type { Organization } from "@/types";

export function useOrganizations(params?: { search?: string; plan?: string }) {
  return useQuery({
    queryKey: ["organizations", params],
    queryFn: () => organizationsService.list(params),
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Organization>) => organizationsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}

export function useUpdateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Organization> }) =>
      organizationsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
    },
  });
}
