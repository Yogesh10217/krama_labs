"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { AnimatePresence, motion } from "framer-motion";
import { Search, CornerDownLeft, ArrowUp, ArrowDown, Command as CommandIcon } from "lucide-react";
import {
  COMMAND_GROUP_LABELS,
  NAV_SECTIONS,
  PALETTE_ACCOUNT,
  PALETTE_DOCUMENTS,
  QUICK_ACTIONS,
} from "@/config/navigation";
import type { CommandItem } from "@/types/navigation";
import { useCommandPalette } from "@/providers/command-palette-provider";
import { Kbd } from "@/components/ui/kbd";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;
const GROUP_ORDER = ["actions", "navigation", "documents", "account"] as const;

/** Flatten sidebar nav into palette entries so the two never drift. */
const NAVIGATION_ITEMS: CommandItem[] = NAV_SECTIONS.flatMap((section) =>
  section.items.map((item) => ({
    id: `nav-${item.id}`,
    label: item.label,
    hint: item.href,
    icon: item.icon,
    group: "navigation" as const,
    href: item.href,
    keywords: [...(item.keywords ?? []), section.label.toLowerCase()],
  }))
);

const ALL_ITEMS: CommandItem[] = [
  ...QUICK_ACTIONS,
  ...NAVIGATION_ITEMS,
  ...PALETTE_DOCUMENTS,
  ...PALETTE_ACCOUNT,
];

function matches(item: CommandItem, query: string) {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const haystack = [item.label, item.hint ?? "", ...(item.keywords ?? [])]
    .join(" ")
    .toLowerCase();
  // Every whitespace-separated token must appear somewhere.
  return q.split(/\s+/).every((token) => haystack.includes(token));
}

export function CommandPalette() {
  const { open, setOpen } = useCommandPalette();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  /** Filtered + grouped, preserving a stable flat order for keyboard nav. */
  const { grouped, flat } = useMemo(() => {
    const filtered = ALL_ITEMS.filter((item) => matches(item, query));
    const grouped = GROUP_ORDER.map((groupId) => ({
      id: groupId,
      label: COMMAND_GROUP_LABELS[groupId],
      items: filtered.filter((item) => item.group === groupId),
    })).filter((group) => group.items.length > 0);
    return { grouped, flat: grouped.flatMap((g) => g.items) };
  }, [query]);

  // Reset transient state whenever the palette opens.
  useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIndex(0);
    }
  }, [open]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  // Keep the highlighted row scrolled into view.
  useEffect(() => {
    const node = listRef.current?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`);
    node?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  const runItem = (item: CommandItem | undefined) => {
    if (!item) return;
    setOpen(false);
    if (item.href && item.href !== "#") router.push(item.href);
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (flat.length ? (i + 1) % flat.length : 0));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => (flat.length ? (i - 1 + flat.length) % flat.length : 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      runItem(flat[activeIndex]);
    }
  };

  return (
    <DialogPrimitive.Root open={open} onOpenChange={setOpen}>
      <AnimatePresence>
        {open && (
          <DialogPrimitive.Portal forceMount>
            {/* Overlay */}
            <DialogPrimitive.Overlay asChild forceMount>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="fixed inset-0 z-[80] bg-background/70 backdrop-blur-sm"
              />
            </DialogPrimitive.Overlay>

            {/* Panel */}
            <DialogPrimitive.Content asChild forceMount onKeyDown={onKeyDown}>
              <motion.div
                initial={{ opacity: 0, y: -12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.22, ease: EASE }}
                className="glass-strong gradient-border fixed left-1/2 top-[12vh] z-[90] w-[calc(100%-2rem)] max-w-[620px] -translate-x-1/2 overflow-hidden rounded-2xl shadow-2xl"
              >
                <DialogPrimitive.Title className="sr-only">
                  Command palette
                </DialogPrimitive.Title>
                <DialogPrimitive.Description className="sr-only">
                  Search pages, documents, and quick actions. Use arrow keys to navigate and Enter to select.
                </DialogPrimitive.Description>

                {/* Input row */}
                <div className="flex items-center gap-3 border-b border-foreground/[0.07] px-4">
                  <Search className="h-4 w-4 shrink-0 text-foreground/35" aria-hidden="true" />
                  <input
                    autoFocus
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search pages, documents, or run a command…"
                    aria-label="Search pages, documents, or run a command"
                    aria-controls="command-list"
                    aria-activedescendant={flat[activeIndex] ? `cmd-${flat[activeIndex].id}` : undefined}
                    className="h-14 w-full bg-transparent text-[15px] text-foreground placeholder:text-foreground/35 focus:outline-none"
                  />
                  <Kbd className="shrink-0">ESC</Kbd>
                </div>

                {/* Results */}
                <div
                  ref={listRef}
                  id="command-list"
                  role="listbox"
                  aria-label="Command results"
                  className="custom-scrollbar max-h-[min(420px,50vh)] overflow-y-auto p-2"
                >
                  {grouped.length === 0 ? (
                    <div className="flex flex-col items-center gap-2 py-12 text-center">
                      <div className="glass flex h-11 w-11 items-center justify-center rounded-xl">
                        <Search className="h-4 w-4 text-foreground/35" aria-hidden="true" />
                      </div>
                      <p className="text-sm font-medium">No results found</p>
                      <p className="max-w-[280px] text-xs text-foreground/45">
                        Nothing matches &ldquo;{query}&rdquo;. Try a page name, a document id, or an action.
                      </p>
                    </div>
                  ) : (
                    grouped.map((group) => {
                      const offset = flat.indexOf(group.items[0]);
                      return (
                        <div key={group.id} className="mb-1 last:mb-0">
                          <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-foreground/35">
                            {group.label}
                          </div>
                          <div role="group" aria-label={group.label}>
                            {group.items.map((item, i) => {
                              const index = offset + i;
                              const isActive = index === activeIndex;
                              return (
                                <button
                                  key={item.id}
                                  id={`cmd-${item.id}`}
                                  data-index={index}
                                  role="option"
                                  aria-selected={isActive}
                                  onMouseMove={() => setActiveIndex(index)}
                                  onClick={() => runItem(item)}
                                  className={cn(
                                    "relative flex w-full items-center gap-3 rounded-xl px-2.5 py-2.5 text-left transition-colors",
                                    isActive ? "text-foreground" : "text-foreground/70"
                                  )}
                                >
                                  {isActive && (
                                    <motion.span
                                      layoutId="cmd-highlight"
                                      className="absolute inset-0 rounded-xl bg-foreground/[0.06] ring-1 ring-inset ring-foreground/[0.08]"
                                      transition={{ type: "spring", stiffness: 500, damping: 40 }}
                                    />
                                  )}
                                  <span
                                    className={cn(
                                      "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors",
                                      isActive ? "ai-gradient-bg text-white" : "glass text-foreground/60"
                                    )}
                                  >
                                    <item.icon className="h-4 w-4" aria-hidden="true" />
                                  </span>
                                  <span className="relative z-10 min-w-0 flex-1">
                                    <span className="block truncate text-[13.5px] font-medium">
                                      {item.label}
                                    </span>
                                    {item.hint && (
                                      <span className="mt-0.5 block truncate text-[11px] text-foreground/40">
                                        {item.hint}
                                      </span>
                                    )}
                                  </span>
                                  {item.shortcut && (
                                    <span className="relative z-10 flex shrink-0 gap-1">
                                      {item.shortcut.map((key) => (
                                        <Kbd key={key}>{key}</Kbd>
                                      ))}
                                    </span>
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* Footer legend */}
                <div className="flex items-center justify-between border-t border-foreground/[0.07] px-4 py-2.5">
                  <div className="flex items-center gap-3.5">
                    <span className="flex items-center gap-1.5 text-[11px] text-foreground/40">
                      <Kbd><ArrowUp className="h-2.5 w-2.5" /></Kbd>
                      <Kbd><ArrowDown className="h-2.5 w-2.5" /></Kbd>
                      navigate
                    </span>
                    <span className="flex items-center gap-1.5 text-[11px] text-foreground/40">
                      <Kbd><CornerDownLeft className="h-2.5 w-2.5" /></Kbd>
                      select
                    </span>
                  </div>
                  <span className="flex items-center gap-1.5 text-[11px] text-foreground/40">
                    <CommandIcon className="h-3 w-3" aria-hidden="true" />
                    Krama Command
                  </span>
                </div>
              </motion.div>
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        )}
      </AnimatePresence>
    </DialogPrimitive.Root>
  );
}
