"use client";

import Link from "next/link";
import {
  UserCircle,
  Settings,
  ShieldCheck,
  Bell,
  KeyRound,
  SlidersHorizontal,
  LifeBuoy,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Kbd } from "@/components/ui/kbd";
import { CURRENT_USER } from "@/config/navigation";

const MENU_GROUPS = [
  [
    { label: "My Profile", href: "/settings#general", icon: UserCircle, shortcut: ["P"] },
    { label: "Account Settings", href: "/settings#general", icon: Settings },
    { label: "Security", href: "/settings#general", icon: ShieldCheck },
  ],
  [
    { label: "Notifications", href: "/settings#general", icon: Bell },
    { label: "API Keys", href: "/settings#api", icon: KeyRound },
    { label: "Appearance", href: "/settings#general", icon: SlidersHorizontal },
  ],
  [{ label: "Help & Support", href: "#", icon: LifeBuoy }],
];

export function UserMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="group flex items-center gap-1.5 rounded-full p-0.5 transition-colors hover:bg-foreground/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={`Account menu for ${CURRENT_USER.name}`}
        >
          <span className="relative">
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full ai-gradient-bg opacity-0 blur-md transition-opacity duration-500 group-hover:opacity-60"
            />
            <Avatar className="relative h-8 w-8 border-foreground/10">
              <AvatarFallback className="bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)] text-[11px] font-semibold text-white">
                {CURRENT_USER.initials}
              </AvatarFallback>
            </Avatar>
          </span>
          <ChevronDown
            className="hidden h-3 w-3 text-foreground/35 transition-transform duration-300 group-data-[state=open]:rotate-180 sm:block"
            aria-hidden="true"
          />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={10}
        className="glass-strong gradient-border w-[268px] overflow-hidden rounded-2xl border-0 p-1.5"
      >
        {/* Identity header */}
        <div className="flex items-center gap-3 rounded-xl px-2.5 py-3">
          <span className="relative shrink-0">
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full ai-gradient-bg opacity-45 blur-md"
            />
            <Avatar className="relative h-10 w-10 border-foreground/10">
              <AvatarFallback className="bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)] text-xs font-semibold text-white">
                {CURRENT_USER.initials}
              </AvatarFallback>
            </Avatar>
          </span>
          <div className="min-w-0">
            <p className="truncate text-[13px] font-semibold leading-tight">
              {CURRENT_USER.name}
            </p>
            <p className="mt-0.5 truncate text-[11px] text-foreground/45">
              {CURRENT_USER.email}
            </p>
            <span className="mt-1.5 inline-flex rounded-full bg-primary/12 px-1.5 py-0.5 text-[9.5px] font-semibold uppercase tracking-wider text-primary">
              {CURRENT_USER.role}
            </span>
          </div>
        </div>

        {MENU_GROUPS.map((group, gi) => (
          <div key={gi}>
            <DropdownMenuSeparator className="my-1 bg-foreground/[0.07]" />
            <DropdownMenuGroup>
              {group.map((item) => (
                <DropdownMenuItem
                  key={item.label}
                  asChild
                  className="cursor-pointer gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-foreground/75 focus:bg-foreground/[0.06] focus:text-foreground"
                >
                  <Link href={item.href}>
                    <item.icon className="h-3.5 w-3.5 text-foreground/45" aria-hidden="true" />
                    <span className="flex-1">{item.label}</span>
                    {"shortcut" in item && item.shortcut && (
                      <span className="flex gap-1">
                        {item.shortcut.map((k) => (
                          <Kbd key={k}>{k}</Kbd>
                        ))}
                      </span>
                    )}
                  </Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuGroup>
          </div>
        ))}

        <DropdownMenuSeparator className="my-1 bg-foreground/[0.07]" />
        <DropdownMenuItem
          asChild
          className="cursor-pointer gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-red-500 focus:bg-red-500/10 focus:text-red-500"
        >
          <Link href="/login">
            <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Log out</span>
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
