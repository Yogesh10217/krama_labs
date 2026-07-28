import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsService } from "@/services/jobs.service";

export function useJobs(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["jobs", params],
    queryFn: () => jobsService.list(params),
    refetchInterval: 5000, // Poll every 5 seconds for running job progress
  });
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => jobsService.getById(jobId),
    enabled: Boolean(jobId),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 3000 : false),
  });
}

export function useSubmitJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { documentId: string; jobType: string; priority?: number }) => jobsService.submit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => jobsService.cancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useQueueHealth() {
  return useQuery({
    queryKey: ["queue-health"],
    queryFn: () => jobsService.getQueueHealth(),
    refetchInterval: 10000,
  });
}
