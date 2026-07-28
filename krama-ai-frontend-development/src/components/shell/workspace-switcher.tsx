"use client";

import { useState } from "react";
import { Building2, Check, ChevronsUpDown, Plus, Settings2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { WORKSPACES } from "@/config/navigation";
import { cn } from "@/lib/utils";

const PLAN_TONE: Record<string, string> = {
  Enterprise: "bg-primary/12 text-primary",
  Pro: "bg-purple-500/12 text-purple-500 dark:text-purple-400",
  Startup: "bg-sky-500/12 text-sky-600 dark:text-sky-400",
};

export function WorkspaceSwitcher({ compact = false }: { compact?: boolean }) {
  const [active, setActive] = useState(WORKSPACES[0]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`Switch workspace. Current: ${active.name}`}
          className={cn(
            "group flex items-center gap-2 rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            compact
              ? "h-9 w-9 justify-center glass hover:bg-foreground/[0.06]"
              : "glass h-9 w-full justify-between px-2.5 hover:bg-foreground/[0.05]"
          )}
        >
          <span className="flex min-w-0 items-center gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)]">
              <Building2 className="h-3 w-3 text-white" aria-hidden="true" />
            </span>
            {!compact && (
              <span className="truncate text-[12.5px] font-medium">{active.name}</span>
            )}
          </span>
          {!compact && (
            <ChevronsUpDown
              className="h-3.5 w-3.5 shrink-0 text-foreground/30 transition-colors group-hover:text-foreground/55"
              aria-hidden="true"
            />
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        sideOffset={8}
        className="glass-strong gradient-border w-[260px] overflow-hidden rounded-2xl border-0 p-1.5"
      >
        <div className="px-2.5 py-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-foreground/35">
          Workspaces
        </div>

        {WORKSPACES.map((workspace) => {
          const isActive = workspace.id === active.id;
          return (
            <DropdownMenuItem
              key={workspace.id}
              onClick={() => setActive(workspace)}
              className="cursor-pointer gap-2.5 rounded-xl px-2.5 py-2 focus:bg-foreground/[0.06]"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)]">
                <Building2 className="h-3.5 w-3.5 text-white" aria-hidden="true" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] font-medium">{workspace.name}</span>
                <span className="mt-0.5 block truncate text-[10.5px] text-foreground/40">
                  {workspace.domain}
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-1.5">
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider",
                    PLAN_TONE[workspace.plan]
                  )}
                >
                  {workspace.plan}
                </span>
                {isActive && <Check className="h-3.5 w-3.5 text-primary" aria-hidden="true" />}
              </span>
            </DropdownMenuItem>
          );
        })}

        <DropdownMenuSeparator className="my-1 bg-foreground/[0.07]" />
        <DropdownMenuItem className="cursor-pointer gap-2.5 rounded-lg px-2.5 py-2 text-[12.5px] text-foreground/60 focus:bg-foreground/[0.06] focus:text-foreground">
          <Plus className="h-3.5 w-3.5" aria-hidden="true" /> Create workspace
        </DropdownMenuItem>
        <DropdownMenuItem className="cursor-pointer gap-2.5 rounded-lg px-2.5 py-2 text-[12.5px] text-foreground/60 focus:bg-foreground/[0.06] focus:text-foreground">
          <Settings2 className="h-3.5 w-3.5" aria-hidden="true" /> Workspace settings
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
