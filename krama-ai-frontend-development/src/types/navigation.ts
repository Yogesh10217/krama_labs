import type { ComponentType } from "react";

/* ------------------------------------------------------------------ *
 * Navigation
 * ------------------------------------------------------------------ */

export interface NavItem {
  /** Stable id — also used as the command-palette key. */
  id: string;
  label: string;
  href: string;
  icon: ComponentType<any>;
  /** Optional count rendered as a pill on the right. */
  badge?: number;
  /** Extra terms that should match this item in the command palette. */
  keywords?: string[];
  /** Nested items — rendered as a collapsible group when expanded. */
  children?: NavChildItem[];
}

export interface NavChildItem {
  id: string;
  label: string;
  href: string;
}

export interface NavSection {
  id: string;
  /** Rendered as an uppercase label when the sidebar is expanded. */
  label: string;
  items: NavItem[];
}

/* ------------------------------------------------------------------ *
 * Command palette
 * ------------------------------------------------------------------ */

export type CommandGroupId = "actions" | "navigation" | "documents" | "account";

export interface CommandItem {
  id: string;
  label: string;
  /** Secondary line, e.g. a document id or a path. */
  hint?: string;
  icon: ComponentType<any>;
  group: CommandGroupId;
  href?: string;
  keywords?: string[];
  /** Rendered on the right as a shortcut chip, e.g. ["G", "D"]. */
  shortcut?: string[];
}

/* ------------------------------------------------------------------ *
 * Notifications
 * ------------------------------------------------------------------ */

export type NotificationKind =
  | "success"
  | "warning"
  | "error"
  | "system"
  | "processing";

export interface AppNotification {
  id: string;
  kind: NotificationKind;
  title: string;
  description: string;
  timestamp: string;
  href?: string;
  read: boolean;
}

/* ------------------------------------------------------------------ *
 * Activity + org + user
 * ------------------------------------------------------------------ */

export interface ActivityEntry {
  id: string;
  actor: string;
  action: string;
  target: string;
  timestamp: string;
  href?: string;
}

export interface Workspace {
  id: string;
  name: string;
  plan: "Startup" | "Pro" | "Enterprise";
  domain: string;
}

export interface SessionUser {
  name: string;
  email: string;
  role: string;
  initials: string;
}
