"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { History, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { RECENT_ACTIVITY } from "@/config/navigation";

const EASE = [0.22, 1, 0.36, 1] as const;

export function RecentActivity() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="hidden h-9 w-9 text-foreground/60 transition-colors hover:text-foreground sm:inline-flex"
          aria-label="Recent activity"
        >
          <History className="h-4 w-4" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={10}
        className="glass-strong gradient-border w-[min(340px,calc(100vw-2rem))] overflow-hidden rounded-2xl border-0 p-0"
      >
        <div className="px-4 pb-2 pt-3.5">
          <h2 className="text-sm font-semibold tracking-tight">Recent Activity</h2>
          <p className="mt-0.5 text-[11px] text-foreground/45">
            Latest events across this workspace
          </p>
        </div>

        <div className="relative border-t border-foreground/[0.06] py-2">
          {/* Timeline rail */}
          <span
            aria-hidden="true"
            className="absolute bottom-4 left-[26px] top-4 w-px bg-foreground/[0.08]"
          />
          {RECENT_ACTIVITY.map((entry, i) => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25, delay: i * 0.04, ease: EASE }}
            >
              <Link
                href={entry.href ?? "#"}
                className="group relative flex items-start gap-3 px-4 py-2 transition-colors hover:bg-foreground/[0.04] focus-visible:bg-foreground/[0.04] focus-visible:outline-none"
              >
                <span className="relative z-10 mt-1.5 flex h-1.5 w-1.5 shrink-0 rounded-full ai-gradient-bg ring-4 ring-background" />
                <span className="min-w-0 flex-1">
                  <span className="block text-[12.5px] leading-snug text-foreground/70">
                    <span className="font-medium text-foreground">{entry.actor}</span>{" "}
                    {entry.action}{" "}
                    <span className="font-medium text-foreground/85">{entry.target}</span>
                  </span>
                  <span className="mt-0.5 block text-[10.5px] text-foreground/35">
                    {entry.timestamp}
                  </span>
                </span>
              </Link>
            </motion.div>
          ))}
        </div>

        <div className="border-t border-foreground/[0.06] p-2">
          <Button variant="ghost" size="sm" className="h-8 w-full gap-1.5 text-xs text-foreground/60" asChild>
            <Link href="/settings#audit">
              View full audit log <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
