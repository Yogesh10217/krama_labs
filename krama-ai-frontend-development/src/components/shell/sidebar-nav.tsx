"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { NAV_SECTIONS } from "@/config/navigation";
import type { NavItem } from "@/types/navigation";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;

function isItemActive(pathname: string, item: NavItem) {
  if (item.href === "/dashboard") return pathname === "/dashboard";
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

interface SidebarNavProps {
  collapsed: boolean;
  onNavigate?: () => void;
}

export function SidebarNav({ collapsed, onNavigate }: SidebarNavProps) {
  const pathname = usePathname();
  const [expandedIds, setExpandedIds] = useState<string[]>(() =>
    NAV_SECTIONS.flatMap((s) => s.items)
      .filter((i) => i.children && pathname.startsWith(i.href))
      .map((i) => i.id)
  );

  const toggleExpanded = (id: string) =>
    setExpandedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  return (
    <nav
      aria-label="Primary"
      className="custom-scrollbar flex-1 overflow-y-auto overflow-x-hidden px-3 py-4"
    >
      {NAV_SECTIONS.map((section, sectionIndex) => (
        <div key={section.id} className={cn(sectionIndex > 0 && "mt-6")}>
          {/* Section label / divider */}
          {collapsed ? (
            sectionIndex > 0 && (
              <div className="mx-2 mb-3 h-px bg-foreground/[0.07]" aria-hidden="true" />
            )
          ) : (
            <div className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-foreground/30">
              {section.label}
            </div>
          )}

          <ul className="space-y-0.5">
            {section.items.map((item) => {
              const active = isItemActive(pathname, item);
              const hasChildren = Boolean(item.children?.length);
              const isExpanded = expandedIds.includes(item.id);

              const row = (
                <div
                  className={cn(
                    "group relative flex items-center rounded-xl transition-colors",
                    collapsed ? "h-10 justify-center" : "h-9 gap-2.5 px-2.5",
                    active
                      ? "text-white"
                      : "text-foreground/55 hover:bg-foreground/[0.05] hover:text-foreground"
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="sidebar-active-pill"
                      className="absolute inset-0 rounded-xl ai-gradient-bg shadow-[0_0_18px_hsl(262_90%_65%_/_0.3)]"
                      transition={{ type: "spring", stiffness: 380, damping: 34 }}
                    />
                  )}
                  <item.icon
                    className="relative z-10 h-[17px] w-[17px] shrink-0"
                    aria-hidden="true"
                  />
                  {!collapsed && (
                    <>
                      <span className="relative z-10 flex-1 truncate text-[13px] font-medium">
                        {item.label}
                      </span>
                      {item.badge !== undefined && (
                        <span
                          className={cn(
                            "relative z-10 flex h-[18px] min-w-[18px] items-center justify-center rounded-full px-1 text-[10px] font-semibold",
                            active
                              ? "bg-white/22 text-white"
                              : "bg-foreground/[0.08] text-foreground/55"
                          )}
                        >
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                  {collapsed && item.badge !== undefined && (
                    <span
                      className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full ai-gradient-bg ring-2 ring-sidebar"
                      aria-hidden="true"
                    />
                  )}
                </div>
              );

              return (
                <li key={item.id}>
                  <div className="flex items-center gap-0.5">
                    {collapsed ? (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Link
                            href={item.href}
                            onClick={onNavigate}
                            aria-current={active ? "page" : undefined}
                            className="block flex-1 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          >
                            {row}
                          </Link>
                        </TooltipTrigger>
                        <TooltipContent side="right" sideOffset={10} className="glass-strong border-0">
                          <span className="flex items-center gap-2 text-[12.5px] font-medium">
                            {item.label}
                            {item.badge !== undefined && (
                              <span className="rounded-full bg-foreground/10 px-1.5 text-[10px]">
                                {item.badge}
                              </span>
                            )}
                          </span>
                        </TooltipContent>
                      </Tooltip>
                    ) : (
                      <Link
                        href={item.href}
                        onClick={onNavigate}
                        aria-current={active ? "page" : undefined}
                        className="block flex-1 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        {row}
                      </Link>
                    )}

                    {/* Nested disclosure toggle */}
                    {hasChildren && !collapsed && (
                      <button
                        onClick={() => toggleExpanded(item.id)}
                        aria-expanded={isExpanded}
                        aria-label={`${isExpanded ? "Collapse" : "Expand"} ${item.label} submenu`}
                        className="flex h-9 w-6 shrink-0 items-center justify-center rounded-lg text-foreground/30 transition-colors hover:bg-foreground/[0.06] hover:text-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <motion.span
                          animate={{ rotate: isExpanded ? 90 : 0 }}
                          transition={{ duration: 0.25, ease: EASE }}
                        >
                          <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
                        </motion.span>
                      </button>
                    )}
                  </div>

                  {/* Nested children */}
                  <AnimatePresence initial={false}>
                    {hasChildren && !collapsed && isExpanded && (
                      <motion.ul
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.28, ease: EASE }}
                        className="overflow-hidden"
                      >
                        <div className="relative mt-0.5 space-y-0.5 py-0.5 pl-[19px]">
                          <span
                            aria-hidden="true"
                            className="absolute bottom-1.5 left-[19px] top-1.5 w-px bg-foreground/[0.09]"
                          />
                          {item.children!.map((child) => (
                            <li key={child.id}>
                              <Link
                                href={child.href}
                                onClick={onNavigate}
                                className="group/child relative flex h-8 items-center gap-2.5 rounded-lg pl-4 pr-2.5 text-[12.5px] text-foreground/45 transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                              >
                                <span
                                  aria-hidden="true"
                                  className="absolute left-0 h-1 w-1 rounded-full bg-foreground/20 transition-colors group-hover/child:bg-primary"
                                />
                                <span className="truncate">{child.label}</span>
                              </Link>
                            </li>
                          ))}
                        </div>
                      </motion.ul>
                    )}
                  </AnimatePresence>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}
