"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { BrainCircuit, PanelLeftClose, PanelLeftOpen, X, Sparkles } from "lucide-react";
import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { SidebarNav } from "./sidebar-nav";
import { WorkspaceSwitcher } from "./workspace-switcher";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;
const WIDTH_EXPANDED = 272;
const WIDTH_COLLAPSED = 72;

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

/** Brand lockup — shared between desktop rail and mobile drawer. */
function Brand({ collapsed }: { collapsed: boolean }) {
  return (
    <Link
      href="/dashboard"
      className={cn(
        "flex items-center gap-2.5 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        collapsed && "justify-center"
      )}
      aria-label="Krama AI — go to dashboard"
    >
      <span className="relative shrink-0">
        <span
          aria-hidden="true"
          className="absolute inset-0 rounded-lg ai-gradient-bg opacity-60 blur-md"
        />
        <span className="relative flex rounded-lg bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)] p-1.5 text-white shadow-lg">
          <BrainCircuit className="h-[18px] w-[18px]" aria-hidden="true" />
        </span>
      </span>
      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.2, ease: EASE }}
            className="overflow-hidden whitespace-nowrap text-[15px] font-semibold tracking-tight"
          >
            <span className="ai-gradient-text">Krama</span>{" "}
            <span className="text-foreground/90">AI</span>
          </motion.span>
        )}
      </AnimatePresence>
    </Link>
  );
}

/** Shared inner content so desktop + mobile stay identical. */
function SidebarBody({
  collapsed,
  onNavigate,
}: {
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  return (
    <>
      <div className={cn("px-3 pb-3", collapsed && "px-2")}>
        <WorkspaceSwitcher compact={collapsed} />
      </div>

      <SidebarNav collapsed={collapsed} onNavigate={onNavigate} />

      {/* Upgrade / usage card */}
      <div className={cn("shrink-0 p-3", collapsed && "px-2")}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Link
                href="/settings#billing"
                className="glass flex h-10 w-full items-center justify-center rounded-xl text-foreground/55 transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label="Enterprise plan — view usage"
              >
                <Sparkles className="h-4 w-4" aria-hidden="true" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={10} className="glass-strong border-0">
              <span className="text-[12.5px] font-medium">Enterprise · 68% quota used</span>
            </TooltipContent>
          </Tooltip>
        ) : (
          <div className="glass gradient-border relative overflow-hidden rounded-xl p-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
              <span className="text-[12px] font-semibold">Enterprise Plan</span>
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-foreground/45">
              142,394 of 200,000 monthly documents used.
            </p>
            <div
              className="mt-2.5 h-1 overflow-hidden rounded-full bg-foreground/[0.08]"
              role="progressbar"
              aria-valuenow={68}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Monthly document quota"
            >
              <motion.div
                className="h-full rounded-full ai-gradient-bg"
                initial={{ width: 0 }}
                animate={{ width: "68%" }}
                transition={{ duration: 1, ease: EASE, delay: 0.3 }}
              />
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export function Sidebar({
  collapsed,
  onToggleCollapsed,
  mobileOpen,
  onCloseMobile,
}: SidebarProps) {
  return (
    <TooltipProvider delayDuration={200}>
      {/* ---------------- Desktop rail ---------------- */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? WIDTH_COLLAPSED : WIDTH_EXPANDED }}
        transition={{ type: "spring", stiffness: 320, damping: 34 }}
        className="glass-strong relative z-20 hidden shrink-0 flex-col border-r-0 md:flex"
        aria-label="Sidebar"
      >
        <div
          className={cn(
            "flex h-16 shrink-0 items-center border-b border-foreground/[0.06]",
            collapsed ? "justify-center px-2" : "justify-between px-4"
          )}
        >
          <Brand collapsed={collapsed} />
          {!collapsed && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onToggleCollapsed}
                  aria-label="Collapse sidebar"
                  className="flex h-7 w-7 items-center justify-center rounded-lg text-foreground/35 transition-colors hover:bg-foreground/[0.06] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={10} className="glass-strong border-0">
                <span className="text-[12.5px]">Collapse sidebar</span>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        <SidebarBody collapsed={collapsed} />

        {collapsed && (
          <div className="shrink-0 border-t border-foreground/[0.06] p-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onToggleCollapsed}
                  aria-label="Expand sidebar"
                  className="flex h-9 w-full items-center justify-center rounded-lg text-foreground/35 transition-colors hover:bg-foreground/[0.06] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <PanelLeftOpen className="h-4 w-4" aria-hidden="true" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={10} className="glass-strong border-0">
                <span className="text-[12.5px]">Expand sidebar</span>
              </TooltipContent>
            </Tooltip>
          </div>
        )}
      </motion.aside>

      {/* ---------------- Mobile drawer ---------------- */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              onClick={onCloseMobile}
              className="fixed inset-0 z-[60] bg-background/70 backdrop-blur-sm md:hidden"
              aria-hidden="true"
            />
            <motion.aside
              key="mobile-drawer"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 340, damping: 36 }}
              className="glass-strong fixed inset-y-0 left-0 z-[70] flex w-[286px] flex-col md:hidden"
              role="dialog"
              aria-modal="true"
              aria-label="Navigation menu"
            >
              <div className="flex h-16 shrink-0 items-center justify-between border-b border-foreground/[0.06] px-4">
                <Brand collapsed={false} />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onCloseMobile}
                  aria-label="Close navigation menu"
                  className="h-8 w-8 text-foreground/50"
                >
                  <X className="h-4 w-4" aria-hidden="true" />
                </Button>
              </div>
              <SidebarBody collapsed={false} onNavigate={onCloseMobile} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </TooltipProvider>
  );
}
