"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  Loader2,
  CheckCheck,
  Inbox,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { NOTIFICATIONS } from "@/config/navigation";
import type { AppNotification, NotificationKind } from "@/types/navigation";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;

const KIND_STYLES: Record<
  NotificationKind,
  { icon: typeof CheckCircle2; tone: string; label: string }
> = {
  success: { icon: CheckCircle2, tone: "bg-emerald-500/12 text-emerald-600 dark:text-emerald-400", label: "Success" },
  warning: { icon: AlertTriangle, tone: "bg-amber-500/12 text-amber-600 dark:text-amber-400", label: "Warning" },
  error: { icon: XCircle, tone: "bg-red-500/12 text-red-600 dark:text-red-400", label: "Error" },
  system: { icon: Info, tone: "bg-sky-500/12 text-sky-600 dark:text-sky-400", label: "System" },
  processing: { icon: Loader2, tone: "bg-primary/12 text-primary", label: "Processing" },
};

const FILTERS = [
  { id: "all", label: "All" },
  { id: "unread", label: "Unread" },
  { id: "system", label: "System" },
] as const;

type FilterId = (typeof FILTERS)[number]["id"];

export function NotificationCenter() {
  const [items, setItems] = useState<AppNotification[]>(NOTIFICATIONS);
  const [filter, setFilter] = useState<FilterId>("all");

  const unreadCount = items.filter((n) => !n.read).length;

  const visible = useMemo(() => {
    if (filter === "unread") return items.filter((n) => !n.read);
    if (filter === "system") return items.filter((n) => n.kind === "system" || n.kind === "processing");
    return items;
  }, [items, filter]);

  const markAllRead = () => setItems((prev) => prev.map((n) => ({ ...n, read: true })));
  const markRead = (id: string) =>
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 text-foreground/60 transition-colors hover:text-foreground"
          aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          <AnimatePresence>
            {unreadCount > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 25 }}
                className="absolute right-1 top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full ai-gradient-bg px-1 text-[9px] font-semibold text-white ring-2 ring-background"
              >
                {unreadCount}
              </motion.span>
            )}
          </AnimatePresence>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={10}
        className="glass-strong gradient-border w-[min(400px,calc(100vw-2rem))] overflow-hidden rounded-2xl border-0 p-0"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 pb-2.5 pt-3.5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold tracking-tight">Notifications</h2>
            {unreadCount > 0 && (
              <span className="rounded-full bg-foreground/[0.07] px-1.5 py-0.5 text-[10px] font-medium text-foreground/55">
                {unreadCount} new
              </span>
            )}
          </div>
          <button
            onClick={markAllRead}
            disabled={unreadCount === 0}
            className="flex items-center gap-1.5 rounded-md px-1.5 py-1 text-[11px] font-medium text-foreground/50 transition-colors hover:text-foreground disabled:pointer-events-none disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <CheckCheck className="h-3 w-3" aria-hidden="true" /> Mark all read
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-1 px-3 pb-2" role="tablist" aria-label="Filter notifications">
          {FILTERS.map((f) => {
            const active = f.id === filter;
            return (
              <button
                key={f.id}
                role="tab"
                aria-selected={active}
                onClick={() => setFilter(f.id)}
                className={cn(
                  "relative rounded-lg px-2.5 py-1 text-[11.5px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  active ? "text-white" : "text-foreground/50 hover:text-foreground/80"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="notif-filter"
                    className="absolute inset-0 rounded-lg ai-gradient-bg"
                    transition={{ type: "spring", stiffness: 400, damping: 34 }}
                  />
                )}
                <span className="relative z-10">{f.label}</span>
              </button>
            );
          })}
        </div>

        {/* List */}
        <div className="custom-scrollbar max-h-[min(400px,55vh)] overflow-y-auto border-t border-foreground/[0.06]">
          <AnimatePresence initial={false} mode="popLayout">
            {visible.length === 0 ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-2 py-12 text-center"
              >
                <div className="glass flex h-11 w-11 items-center justify-center rounded-xl">
                  <Inbox className="h-4 w-4 text-foreground/35" aria-hidden="true" />
                </div>
                <p className="text-sm font-medium">You&apos;re all caught up</p>
                <p className="text-xs text-foreground/45">No notifications in this view.</p>
              </motion.div>
            ) : (
              visible.map((n, i) => {
                const style = KIND_STYLES[n.kind];
                const Icon = style.icon;
                return (
                  <motion.div
                    key={n.id}
                    layout
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 8 }}
                    transition={{ duration: 0.24, delay: i * 0.03, ease: EASE }}
                  >
                    <Link
                      href={n.href ?? "#"}
                      onClick={() => markRead(n.id)}
                      className={cn(
                        "group relative flex gap-3 px-4 py-3 transition-colors hover:bg-foreground/[0.04] focus-visible:bg-foreground/[0.04] focus-visible:outline-none",
                        !n.read && "bg-primary/[0.035]"
                      )}
                    >
                      {!n.read && (
                        <span
                          className="absolute left-0 top-0 h-full w-[2px] ai-gradient-bg"
                          aria-hidden="true"
                        />
                      )}
                      <span
                        className={cn(
                          "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                          style.tone
                        )}
                      >
                        <Icon
                          className={cn("h-3.5 w-3.5", n.kind === "processing" && "animate-spin")}
                          aria-hidden="true"
                        />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-start justify-between gap-2">
                          <span className="text-[13px] font-medium leading-snug">{n.title}</span>
                          {!n.read && (
                            <span
                              className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                              aria-label="Unread"
                            />
                          )}
                        </span>
                        <span className="mt-0.5 line-clamp-2 block text-[11.5px] leading-relaxed text-foreground/45">
                          {n.description}
                        </span>
                        <span className="mt-1.5 flex items-center gap-2">
                          <span className="text-[10px] uppercase tracking-wider text-foreground/30">
                            {style.label}
                          </span>
                          <span className="h-0.5 w-0.5 rounded-full bg-foreground/20" />
                          <span className="text-[10px] text-foreground/30">{n.timestamp}</span>
                        </span>
                      </span>
                    </Link>
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="border-t border-foreground/[0.06] p-2">
          <Button variant="ghost" size="sm" className="h-8 w-full text-xs text-foreground/60" asChild>
            <Link href="/settings#general">Notification preferences</Link>
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
