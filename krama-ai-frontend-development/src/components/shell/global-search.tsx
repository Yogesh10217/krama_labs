"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { Kbd } from "@/components/ui/kbd";
import { useCommandPalette } from "@/providers/command-palette-provider";
import { cn } from "@/lib/utils";

/**
 * GlobalSearch — a button styled as an input that opens the command palette.
 * Expands on hover/focus for a subtle premium interaction.
 */
export function GlobalSearch() {
  const { setOpen } = useCommandPalette();
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    setIsMac(
      typeof navigator !== "undefined" && /Mac|iPod|iPhone|iPad/.test(navigator.platform)
    );
  }, []);

  return (
    <>
      {/* Desktop: full search affordance */}
      <motion.button
        onClick={() => setOpen(true)}
        whileTap={{ scale: 0.985 }}
        aria-label="Search — open command palette"
        aria-keyshortcuts="Meta+K Control+K"
        className={cn(
          "group hidden h-9 items-center gap-2.5 rounded-xl px-3 md:flex",
          "w-[220px] lg:w-[280px] xl:w-[320px]",
          "glass text-left transition-all duration-300",
          "hover:bg-foreground/[0.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        )}
      >
        <Search
          className="h-3.5 w-3.5 shrink-0 text-foreground/35 transition-colors group-hover:text-foreground/55"
          aria-hidden="true"
        />
        <span className="flex-1 truncate text-[13px] text-foreground/40 transition-colors group-hover:text-foreground/60">
          Search or jump to…
        </span>
        <span className="flex shrink-0 items-center gap-1">
          <Kbd>{isMac ? "⌘" : "Ctrl"}</Kbd>
          <Kbd>K</Kbd>
        </span>
      </motion.button>

      {/* Mobile / tablet: icon only */}
      <button
        onClick={() => setOpen(true)}
        aria-label="Search"
        className="flex h-9 w-9 items-center justify-center rounded-lg text-foreground/60 transition-colors hover:bg-foreground/[0.06] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:hidden"
      >
        <Search className="h-4 w-4" aria-hidden="true" />
      </button>
    </>
  );
}
