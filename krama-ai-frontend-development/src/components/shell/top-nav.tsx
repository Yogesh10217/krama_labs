"use client";

import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { GlobalSearch } from "./global-search";
import { NotificationCenter } from "./notification-center";
import { RecentActivity } from "./recent-activity";
import { QuickActions } from "./quick-actions";
import { UserMenu } from "./user-menu";

interface TopNavProps {
  onOpenMobileNav: () => void;
}

export function TopNav({ onOpenMobileNav }: TopNavProps) {
  return (
    <header
      className="glass-strong sticky top-0 z-40 flex h-16 shrink-0 items-center gap-3 border-b-0 px-3 sm:px-4"
      role="banner"
    >
      {/* Left: mobile trigger + breadcrumbs */}
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onOpenMobileNav}
          aria-label="Open navigation menu"
          className="h-9 w-9 shrink-0 text-foreground/60 md:hidden"
        >
          <Menu className="h-4.5 w-4.5" aria-hidden="true" />
        </Button>

        <div className="hidden min-w-0 md:block">
          <Breadcrumbs />
        </div>
      </div>

      {/* Right: tools */}
      <div className="flex shrink-0 items-center gap-1.5">
        <GlobalSearch />

        <Separator
          orientation="vertical"
          className="mx-0.5 hidden h-5 bg-foreground/[0.08] lg:block"
        />

        <RecentActivity />
        <NotificationCenter />
        <ThemeToggle />

        <Separator
          orientation="vertical"
          className="mx-0.5 hidden h-5 bg-foreground/[0.08] sm:block"
        />

        <QuickActions />
        <UserMenu />
      </div>
    </header>
  );
}
