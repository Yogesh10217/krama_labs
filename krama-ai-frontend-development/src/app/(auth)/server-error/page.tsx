"use client";

import { ServerCrash } from "lucide-react";
import { AuthStatusCard } from "@/features/auth/components/auth-status-card";

export default function ServerErrorPage() {
  return (
    <AuthStatusCard
      icon={ServerCrash}
      tone="danger"
      code="500"
      title="Internal server error"
      description="Something went wrong on our end. Our engineering team has been notified automatically."
      body={
        <div className="glass rounded-xl px-4 py-3 text-left">
          <p className="text-[11px] uppercase tracking-wider text-foreground/35">
            Incident reference
          </p>
          <p className="mt-1 font-mono text-[13px] text-foreground/70">
            req_8f92c41d-7a3e-4b90
          </p>
        </div>
      }
      actions={[
        { label: "Back to Dashboard", href: "/dashboard" },
        { label: "View System Health", href: "/health", variant: "outline" },
      ]}
      footer={
        <p className="text-center text-xs text-foreground/40">
          If this keeps happening, contact your account team with the reference above.
        </p>
      }
    />
  );
}
