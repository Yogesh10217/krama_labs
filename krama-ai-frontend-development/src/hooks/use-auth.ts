import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authService, type LoginCredentials } from "@/services/auth.service";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["current-user"],
    queryFn: () => authService.getMe(),
    staleTime: 1000 * 60 * 15,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentials: LoginCredentials) => authService.login(credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["current-user"] });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      queryClient.clear();
    },
  });
}
