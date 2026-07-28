"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

/**
 * PageContainer — the single source of truth for page gutters and max width.
 * Every dashboard page renders inside this to guarantee consistent rhythm.
 */
export function PageContainer({
  children,
  size = "default",
  className,
}: {
  children: React.ReactNode;
  /** "default" = data pages (1400px), "wide" = dashboard/analytics (1600px), "narrow" = settings (896px) */
  size?: "default" | "wide" | "narrow";
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-6 md:p-8 pb-20 mx-auto space-y-6 w-full",
        size === "wide" && "max-w-[1600px]",
        size === "default" && "max-w-[1400px]",
        size === "narrow" && "max-w-4xl",
        className
      )}
    >
      {children}
    </div>
  );
}

/**
 * PageHeader — unified page title block with optional action slot.
 * Replaces every hand-rolled header across the app.
 */
export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
    >
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="text-muted-foreground mt-1">{description}</p>
      </div>
      {children && <div className="flex flex-wrap items-center gap-3">{children}</div>}
    </motion.div>
  );
}
