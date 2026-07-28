"use client";

import { Clock } from "lucide-react";
import { AuthStatusCard } from "@/features/auth/components/auth-status-card";

export default function SessionExpiredPage() {
  return (
    <AuthStatusCard
      icon={Clock}
      tone="warning"
      title="Session expired"
      description="For your security, you were signed out after a period of inactivity."
      body={
        <p className="text-sm text-foreground/50">
          Any unsaved changes in your workspace were preserved as drafts.
        </p>
      }
      actions={[{ label: "Sign in again", href: "/login" }]}
    />
  );
}
