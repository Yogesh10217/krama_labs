"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;

export type StatusTone = "neutral" | "success" | "warning" | "danger";

const TONE_STYLES: Record<StatusTone, { ring: string; icon: string; accent: string }> = {
  neutral: {
    ring: "bg-foreground/[0.06]",
    icon: "text-foreground/55",
    accent: "",
  },
  success: {
    ring: "bg-emerald-500/12",
    icon: "text-emerald-600 dark:text-emerald-400",
    accent: "from-transparent via-emerald-500/60 to-transparent",
  },
  warning: {
    ring: "bg-amber-500/12",
    icon: "text-amber-600 dark:text-amber-400",
    accent: "from-transparent via-amber-500/60 to-transparent",
  },
  danger: {
    ring: "bg-red-500/12",
    icon: "text-red-600 dark:text-red-400",
    accent: "from-transparent via-red-500/60 to-transparent",
  },
};

export interface AuthStatusAction {
  label: string;
  href?: string;
  onClick?: () => void;
  variant?: "primary" | "outline";
}

interface AuthStatusCardProps {
  icon: LucideIcon;
  tone?: StatusTone;
  /** Large monospace code, e.g. "404". */
  code?: string;
  title: string;
  description: string;
  body?: React.ReactNode;
  actions?: AuthStatusAction[];
  footer?: React.ReactNode;
}

/**
 * AuthStatusCard — shared presentation for every auth/error outcome screen
 * (verification, session expired, 403, 404, 500). Keeps all states visually
 * identical so the product never feels stitched together.
 */
export function AuthStatusCard({
  icon: Icon,
  tone = "neutral",
  code,
  title,
  description,
  body,
  actions = [],
  footer,
}: AuthStatusCardProps) {
  const styles = TONE_STYLES[tone];

  return (
    <Card className="glass-strong gradient-border relative overflow-hidden text-center shadow-2xl">
      {tone !== "neutral" && (
        <span
          aria-hidden="true"
          className={cn("absolute inset-x-0 top-0 h-px bg-gradient-to-r", styles.accent)}
        />
      )}

      <CardHeader className="space-y-4 pb-4 pt-9">
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 280, damping: 18, delay: 0.1 }}
          className="relative mx-auto"
        >
          <span
            aria-hidden="true"
            className="absolute inset-0 rounded-full ai-gradient-bg opacity-25 blur-lg"
          />
          <span
            className={cn(
              "relative flex h-16 w-16 items-center justify-center rounded-full border-4 border-background shadow-inner",
              styles.ring
            )}
          >
            <Icon className={cn("h-7 w-7", styles.icon)} aria-hidden="true" />
          </span>
        </motion.div>

        <div>
          {code && (
            <p className="mb-1.5 font-mono text-xs tracking-[0.2em] text-foreground/35">
              {code}
            </p>
          )}
          <CardTitle className="text-2xl font-semibold tracking-tight">{title}</CardTitle>
          <CardDescription className="mx-auto mt-2 max-w-sm text-[15px] leading-relaxed">
            {description}
          </CardDescription>
        </div>
      </CardHeader>

      {body && <CardContent className="pb-2">{body}</CardContent>}

      {actions.length > 0 && (
        <CardFooter className="flex flex-col gap-2.5 pb-8 pt-4 sm:flex-row">
          {actions.map((action, i) => {
            const isPrimary = (action.variant ?? (i === 0 ? "primary" : "outline")) === "primary";
            const className = isPrimary
              ? "h-11 w-full border-0 ai-gradient-bg font-medium text-white shadow-[0_0_24px_hsl(262_90%_65%_/_0.3)] transition-shadow hover:shadow-[0_0_32px_hsl(262_90%_65%_/_0.45)]"
              : "glass h-11 w-full border-foreground/10 font-medium hover:border-foreground/20 hover:bg-foreground/[0.05]";

            if (action.href) {
              return (
                <Button
                  key={action.label}
                  variant={isPrimary ? "default" : "outline"}
                  className={className}
                  asChild
                >
                  <Link href={action.href}>{action.label}</Link>
                </Button>
              );
            }
            return (
              <Button
                key={action.label}
                variant={isPrimary ? "default" : "outline"}
                className={className}
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            );
          })}
        </CardFooter>
      )}

      {footer && <div className="px-6 pb-8">{footer}</div>}
    </Card>
  );
}

export const authCardTransition = { duration: 0.5, ease: EASE };
