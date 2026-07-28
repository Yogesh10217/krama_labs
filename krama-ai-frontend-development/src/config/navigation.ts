import {
  LayoutDashboard,
  Files,
  UploadCloud,
  ServerCog,
  UserCheck,
  BarChart3,
  FilePieChart,
  Building2,
  Users,
  Network,
  HeartPulse,
  Settings,
  BrainCircuit,
  Plus,
  Search,
  KeyRound,
  ScrollText,
  CreditCard,
  SlidersHorizontal,
  ShieldCheck,
  Bell,
  UserCircle,
  LifeBuoy,
  FileText,
} from "lucide-react";
import type {
  ActivityEntry,
  AppNotification,
  CommandItem,
  NavSection,
  SessionUser,
  Workspace,
} from "@/types/navigation";

/* ------------------------------------------------------------------ *
 * Sidebar navigation — single source of truth.
 * The command palette derives its "navigation" group from this.
 * ------------------------------------------------------------------ */

export const NAV_SECTIONS: NavSection[] = [
  {
    id: "workspace",
    label: "Workspace",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        keywords: ["home", "overview", "start"],
      },
      {
        id: "documents",
        label: "Documents",
        href: "/documents",
        icon: Files,
        keywords: ["files", "library", "pdf"],
      },
      {
        id: "upload",
        label: "Upload",
        href: "/upload",
        icon: UploadCloud,
        keywords: ["ingest", "import", "drop"],
      },
      {
        id: "jobs",
        label: "Processing Jobs",
        href: "/jobs",
        icon: ServerCog,
        badge: 2,
        keywords: ["queue", "batch", "pipeline"],
      },
      {
        id: "review",
        label: "Human Review",
        href: "/review",
        icon: UserCheck,
        badge: 5,
        keywords: ["approve", "validate", "queue"],
      },
    ],
  },
  {
    id: "intelligence",
    label: "Intelligence",
    items: [
      {
        id: "analytics",
        label: "Analytics",
        href: "/analytics",
        icon: BarChart3,
        keywords: ["metrics", "charts", "insights"],
      },
      {
        id: "reports",
        label: "Reports",
        href: "/reports",
        icon: FilePieChart,
        keywords: ["export", "schedule", "pdf"],
      },
      {
        id: "models",
        label: "Models",
        href: "/models",
        icon: BrainCircuit,
        keywords: ["ai", "inference", "fine-tune"],
      },
    ],
  },
  {
    id: "administration",
    label: "Administration",
    items: [
      {
        id: "organizations",
        label: "Organizations",
        href: "/organizations",
        icon: Building2,
        keywords: ["tenants", "workspaces", "accounts"],
      },
      {
        id: "users",
        label: "Users",
        href: "/users",
        icon: Users,
        keywords: ["members", "team", "roles", "permissions"],
      },
      {
        id: "providers",
        label: "Providers",
        href: "/providers",
        icon: Network,
        keywords: ["openai", "anthropic", "routing", "failover"],
      },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      {
        id: "health",
        label: "System Health",
        href: "/health",
        icon: HeartPulse,
        keywords: ["status", "uptime", "workers", "queues"],
      },
      {
        id: "settings",
        label: "Settings",
        href: "/settings",
        icon: Settings,
        keywords: ["preferences", "configuration"],
        children: [
          { id: "settings-general", label: "General", href: "/settings#general" },
          { id: "settings-api", label: "API Keys", href: "/settings#api" },
          { id: "settings-audit", label: "Audit Logs", href: "/settings#audit" },
          { id: "settings-billing", label: "Billing", href: "/settings#billing" },
        ],
      },
    ],
  },
];

/* ------------------------------------------------------------------ *
 * Quick actions — surfaced in the palette and the Quick Actions button.
 * ------------------------------------------------------------------ */

export const QUICK_ACTIONS: CommandItem[] = [
  {
    id: "action-upload",
    label: "Upload documents",
    hint: "Add files to the processing queue",
    icon: UploadCloud,
    group: "actions",
    href: "/upload",
    shortcut: ["U"],
    keywords: ["new", "add", "import", "ingest"],
  },
  {
    id: "action-review",
    label: "Open review queue",
    hint: "5 documents awaiting review",
    icon: UserCheck,
    group: "actions",
    href: "/review",
    shortcut: ["R"],
    keywords: ["approve", "validate"],
  },
  {
    id: "action-report",
    label: "Generate report",
    hint: "Export analytics as PDF or CSV",
    icon: FilePieChart,
    group: "actions",
    href: "/reports",
    keywords: ["export", "download", "csv"],
  },
  {
    id: "action-invite",
    label: "Invite team member",
    hint: "Send a workspace invitation",
    icon: Plus,
    group: "actions",
    href: "/users",
    keywords: ["user", "add", "member", "seat"],
  },
  {
    id: "action-key",
    label: "Create API key",
    hint: "Issue a new secret key",
    icon: KeyRound,
    group: "actions",
    href: "/settings#api",
    keywords: ["token", "secret", "credential"],
  },
];

/* Recent documents surfaced in the palette. */
export const PALETTE_DOCUMENTS: CommandItem[] = [
  { id: "doc-8922", label: "Invoice_XCorp_Q3.pdf", hint: "DOC-8922 · Needs review", icon: FileText, group: "documents", href: "/documents/DOC-8922" },
  { id: "doc-8921", label: "Q4_Financial_Report_Final.pdf", hint: "DOC-8921 · Extracted", icon: FileText, group: "documents", href: "/documents/DOC-8921" },
  { id: "doc-8920", label: "MSA_TechCorp_Signed.docx", hint: "DOC-8920 · Processing", icon: FileText, group: "documents", href: "/documents/DOC-8920" },
  { id: "doc-8919", label: "Employee_Handbook_2025.pdf", hint: "DOC-8919 · Extracted", icon: FileText, group: "documents", href: "/documents/DOC-8919" },
];

/* Account-level palette entries. */
export const PALETTE_ACCOUNT: CommandItem[] = [
  { id: "acct-profile", label: "My Profile", icon: UserCircle, group: "account", href: "/settings#general" },
  { id: "acct-security", label: "Security", icon: ShieldCheck, group: "account", href: "/settings#general" },
  { id: "acct-notifications", label: "Notification preferences", icon: Bell, group: "account", href: "/settings#general" },
  { id: "acct-appearance", label: "Appearance", icon: SlidersHorizontal, group: "account", href: "/settings#general" },
  { id: "acct-billing", label: "Billing", icon: CreditCard, group: "account", href: "/settings#billing" },
  { id: "acct-audit", label: "Audit logs", icon: ScrollText, group: "account", href: "/settings#audit" },
  { id: "acct-help", label: "Help & documentation", icon: LifeBuoy, group: "account", href: "#" },
];

export const COMMAND_GROUP_LABELS: Record<string, string> = {
  actions: "Quick Actions",
  navigation: "Navigation",
  documents: "Documents",
  account: "Account & Settings",
};

export const PALETTE_SEARCH_ICON = Search;

/* ------------------------------------------------------------------ *
 * Placeholder session data (no backend).
 * ------------------------------------------------------------------ */

export const CURRENT_USER: SessionUser = {
  name: "Alice Donovan",
  email: "alice@acmecorp.com",
  role: "Owner",
  initials: "AD",
};

export const WORKSPACES: Workspace[] = [
  { id: "org_1", name: "Acme Corporation", plan: "Enterprise", domain: "acmecorp.com" },
  { id: "org_2", name: "Globex Inc", plan: "Pro", domain: "globex.com" },
  { id: "org_3", name: "Soylent Corp", plan: "Startup", domain: "soylent.io" },
];

export const NOTIFICATIONS: AppNotification[] = [
  {
    id: "n1",
    kind: "warning",
    title: "5 documents need human review",
    description: "Low-confidence extractions detected in the Acme queue.",
    timestamp: "2m ago",
    href: "/review",
    read: false,
  },
  {
    id: "n2",
    kind: "success",
    title: "Batch job completed",
    description: "job_989 processed 2,048 documents with 99.6% accuracy.",
    timestamp: "1h ago",
    href: "/jobs",
    read: false,
  },
  {
    id: "n3",
    kind: "processing",
    title: "Entity linking in progress",
    description: "job_992 is 31% complete — 45 documents remaining.",
    timestamp: "1h ago",
    href: "/jobs",
    read: false,
  },
  {
    id: "n4",
    kind: "error",
    title: "Extraction failed",
    description: "Invoice_Scan_Travel.jpg could not be parsed — image too blurry.",
    timestamp: "3h ago",
    href: "/documents",
    read: true,
  },
  {
    id: "n5",
    kind: "system",
    title: "Provider failover triggered",
    description: "Internal GPU cluster degraded — traffic rerouted to OpenAI.",
    timestamp: "5h ago",
    href: "/providers",
    read: true,
  },
  {
    id: "n6",
    kind: "success",
    title: "Monthly report generated",
    description: "Executive Summary for October is ready to download.",
    timestamp: "Yesterday",
    href: "/reports",
    read: true,
  },
];

export const RECENT_ACTIVITY: ActivityEntry[] = [
  { id: "a1", actor: "You", action: "approved", target: "Invoice_XCorp_Q3.pdf", timestamp: "4m ago", href: "/documents/DOC-8922" },
  { id: "a2", actor: "Ben Kessler", action: "uploaded", target: "12 documents", timestamp: "22m ago", href: "/documents" },
  { id: "a3", actor: "System", action: "completed", target: "job_989", timestamp: "1h ago", href: "/jobs" },
  { id: "a4", actor: "Clara Nguyen", action: "rejected", target: "Receipt_Scan_Travel.jpg", timestamp: "2h ago", href: "/review" },
  { id: "a5", actor: "You", action: "rolled", target: "Production API key", timestamp: "Yesterday", href: "/settings#api" },
];
