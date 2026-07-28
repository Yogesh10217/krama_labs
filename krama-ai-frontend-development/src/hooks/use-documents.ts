/**
 * TanStack Query hooks for the documents domain.
 * Components never call services directly — they use these hooks,
 * which own cache keys, invalidation, and optimistic updates.
 */
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsService } from "@/services/documents.service";
import type { ReviewDecision } from "@/types";

export const documentKeys = {
  all: ["documents"] as const,
  list: (filters: object) => [...documentKeys.all, "list", filters] as const,
  detail: (id: string) => [...documentKeys.all, "detail", id] as const,
};

export function useDocuments(filters: { page?: number; status?: string; search?: string } = {}) {
  return useQuery({
    queryKey: documentKeys.list(filters),
    queryFn: () => documentsService.list(filters),
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: documentKeys.detail(id),
    queryFn: () => documentsService.getById(id),
    enabled: Boolean(id),
  });
}

export function useSubmitReview(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ decision, comment }: { decision: ReviewDecision; comment?: string }) =>
      documentsService.submitReview(id, decision, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: documentKeys.all });
    },
  });
}
