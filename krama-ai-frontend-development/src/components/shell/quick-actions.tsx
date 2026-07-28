"use client";

import Link from "next/link";
import { Plus, Command } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Kbd } from "@/components/ui/kbd";
import { QUICK_ACTIONS } from "@/config/navigation";
import { useCommandPalette } from "@/providers/command-palette-provider";

export function QuickActions() {
  const { setOpen } = useCommandPalette();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          size="sm"
          className="group h-9 gap-1.5 border-0 ai-gradient-bg px-3 text-[13px] font-medium text-white shadow-[0_0_18px_hsl(262_90%_65%_/_0.28)] transition-shadow hover:shadow-[0_0_26px_hsl(262_90%_65%_/_0.42)]"
          aria-label="Quick actions"
        >
          <Plus className="h-3.5 w-3.5 transition-transform duration-300 group-data-[state=open]:rotate-45" aria-hidden="true" />
          <span className="hidden sm:inline">Create</span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={10}
        className="glass-strong gradient-border w-[280px] overflow-hidden rounded-2xl border-0 p-1.5"
      >
        <div className="px-2.5 py-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-foreground/35">
          Quick Actions
        </div>

        {QUICK_ACTIONS.map((action) => (
          <DropdownMenuItem
            key={action.id}
            asChild
            className="cursor-pointer gap-3 rounded-xl px-2.5 py-2.5 focus:bg-foreground/[0.06]"
          >
            <Link href={action.href ?? "#"}>
              <span className="glass flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-foreground/65">
                <action.icon className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] font-medium">{action.label}</span>
                {action.hint && (
                  <span className="mt-0.5 block truncate text-[11px] text-foreground/40">
                    {action.hint}
                  </span>
                )}
              </span>
              {action.shortcut && (
                <span className="flex shrink-0 gap-1">
                  {action.shortcut.map((k) => (
                    <Kbd key={k}>{k}</Kbd>
                  ))}
                </span>
              )}
            </Link>
          </DropdownMenuItem>
        ))}

        <DropdownMenuSeparator className="my-1 bg-foreground/[0.07]" />
        <DropdownMenuItem
          onSelect={(e) => {
            e.preventDefault();
            setOpen(true);
          }}
          className="cursor-pointer gap-3 rounded-xl px-2.5 py-2 text-[12.5px] text-foreground/60 focus:bg-foreground/[0.06] focus:text-foreground"
        >
          <Command className="h-3.5 w-3.5" aria-hidden="true" />
          <span className="flex-1">Browse all commands</span>
          <Kbd>⌘K</Kbd>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
