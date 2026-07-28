import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/**
 * StatusBadge — single mapping from domain statuses to badge variants.
 * Eliminates the per-table ternary chains previously duplicated across
 * Documents, Jobs, Users, Review, and Organizations.
 */

type StatusTone = "success" | "warning" | "destructive" | "secondary";

const STATUS_TONES: Record<string, StatusTone> = {
  // documents
  extracted: "success",
  processing: "warning",
  uploaded: "secondary",
  review: "warning",
  failed: "destructive",
  // jobs
  running: "warning",
  completed: "success",
  paused: "secondary",
  queued: "secondary",
  // users / orgs
  active: "success",
  invited: "warning",
  suspended: "destructive",
  trial: "warning",
  past_due: "destructive",
  // infra
  operational: "success",
  degraded: "warning",
  offline: "destructive",
  ready: "success",
  generating: "warning",
};

export function StatusBadge({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const tone = STATUS_TONES[status.toLowerCase()] ?? "secondary";
  return (
    <Badge variant={tone} className={cn("capitalize", className)}>
      {status.replace(/_/g, " ")}
    </Badge>
  );
}
