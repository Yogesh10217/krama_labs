"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import { AmbientBackground } from "@/components/layout/AmbientBackground";
import { CommandPaletteProvider } from "@/providers/command-palette-provider";
import { CommandPalette } from "./command-palette";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";

const STORAGE_KEY = "krama:sidebar-collapsed";
const EASE = [0.22, 1, 0.36, 1] as const;

/**
 * AppShell — the reusable foundation for every authenticated page.
 *
 * Composition:
 *   AmbientBackground (aurora + grid + noise, shared with marketing)
 *   ├── Sidebar        collapsible rail (desktop) + animated drawer (mobile)
 *   └── Column
 *       ├── TopNav     search · activity · notifications · theme · create · profile
 *       └── <main>     animated page transitions
 *   CommandPalette     global ⌘K overlay
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Restore persisted rail state after mount (avoids hydration mismatch).
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored !== null) setCollapsed(stored === "true");
    } catch {
      /* storage unavailable — fall back to expanded */
    }
  }, []);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        /* non-fatal */
      }
      return next;
    });
  }, []);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Lock body scroll while the drawer is open.
  useEffect(() => {
    if (!mobileOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [mobileOpen]);

  // "[" toggles the sidebar, matching Linear.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "[" || event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName.toLowerCase();
      if (tag === "input" || tag === "textarea" || target?.isContentEditable) return;
      event.preventDefault();
      toggleCollapsed();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [toggleCollapsed]);

  return (
    <MotionConfig reducedMotion="user">
      <CommandPaletteProvider>
        <div className="relative flex h-screen w-full overflow-hidden">
          <AmbientBackground />

          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
          >
            Skip to main content
          </a>

          <Sidebar
            collapsed={collapsed}
            onToggleCollapsed={toggleCollapsed}
            mobileOpen={mobileOpen}
            onCloseMobile={() => setMobileOpen(false)}
          />

          <div className="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden">
            <TopNav
              onOpenMobileNav={() => setMobileOpen(true)}
              onToggleSidebar={toggleCollapsed}
              collapsed={collapsed}
            />

            <main
              id="main-content"
              tabIndex={-1}
              className="relative flex-1 overflow-y-auto focus:outline-none"
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={pathname}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.32, ease: EASE }}
                  className="h-full"
                >
                  {children}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>

          <CommandPalette />
        </div>
      </CommandPaletteProvider>
    </MotionConfig>
  );
}
