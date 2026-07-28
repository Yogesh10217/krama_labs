"use client";

import { ShieldX } from "lucide-react";
import { AuthStatusCard } from "@/features/auth/components/auth-status-card";

export default function UnauthorizedPage() {
  return (
    <AuthStatusCard
      icon={ShieldX}
      tone="danger"
      code="403"
      title="Access denied"
      description="You don't have permission to view this resource in this workspace."
      body={
        <p className="text-sm text-foreground/50">
          Ask an organization administrator to grant your role access, or switch to a
          workspace where you have permission.
        </p>
      }
      actions={[
        { label: "Back to Dashboard", href: "/dashboard" },
        { label: "Sign in as another user", href: "/login", variant: "outline" },
      ]}
    />
  );
}
