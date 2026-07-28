"use client";

import { ErrorState } from "@/components/shared/states";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <ErrorState
        title="Unable to load this page"
        description={error.digest ? `Reference: ${error.digest}` : error.message}
        onRetry={reset}
      />
    </div>
  );
}
