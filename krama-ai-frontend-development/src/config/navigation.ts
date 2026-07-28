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
  { id: "doc-8922", label: "Commercial_Invoice_INV-8922.pdf", hint: "DOC-8922 · Human Review Required", icon: FileText, group: "documents", href: "/documents/DOC-8922" },
  { id: "doc-8921", label: "Q4_Financial_Statement_2025.pdf", hint: "DOC-8921 · OCR & Classification Complete", icon: FileText, group: "documents", href: "/documents/DOC-8921" },
  { id: "doc-8920", label: "Master_Service_Agreement_MSA-8920.pdf", hint: "DOC-8920 · Validation Pending", icon: FileText, group: "documents", href: "/documents/DOC-8920" },
  { id: "doc-8919", label: "Health_Insurance_Claim_CLM-8919.pdf", hint: "DOC-8919 · Approved & Synced", icon: FileText, group: "documents", href: "/documents/DOC-8919" },
];

/* Account-level palette entries. */
export const PALETTE_ACCOUNT: CommandItem[] = [
  { id: "acct-profile", label: "My Profile", icon: UserCircle, group: "account", href: "/settings#general" },
  { id: "acct-security", label: "Security", icon: ShieldCheck, group: "account", href: "/settings#general" },
  { id: "acct-notifications", label: "Notification preferences", icon: Bell, group: "account", href: "/settings#general" },
  { id: "acct-billing", label: "Billing & Quotas", icon: CreditCard, group: "account", href: "/settings#billing" },
  { id: "acct-audit", label: "Audit logs", icon: ScrollText, group: "account", href: "/settings#audit" },
  { id: "acct-help", label: "Help & Documentation", icon: LifeBuoy, group: "account", href: "#" },
];

export const COMMAND_GROUP_LABELS: Record<string, string> = {
  actions: "Quick Actions",
  navigation: "Navigation",
  documents: "Documents",
  account: "Account & Settings",
};

export const PALETTE_SEARCH_ICON = Search;

/* ------------------------------------------------------------------ *
 * Krama AI Enterprise Session Data
 * ------------------------------------------------------------------ */

export const CURRENT_USER: SessionUser = {
  name: "Krama Admin",
  email: "admin@krama.ai",
  role: "Enterprise Admin",
  initials: "KA",
};

export const WORKSPACES: Workspace[] = [
  { id: "org_1", name: "Star Health Insurance", plan: "Enterprise", domain: "starhealth.in" },
  { id: "org_2", name: "ICICI Lombard Claims", plan: "Enterprise", domain: "icicilombard.com" },
  { id: "org_3", name: "HDFC ERGO General", plan: "Enterprise", domain: "hdfcergo.com" },
  { id: "org_4", name: "Bajaj Allianz TPA", plan: "Enterprise", domain: "bajajallianz.com" },
];

export const NOTIFICATIONS: AppNotification[] = [
  {
    id: "n1",
    kind: "warning",
    title: "5 documents require human review",
    description: "Low OCR confidence scores detected in invoice line items.",
    timestamp: "2m ago",
    href: "/review",
    read: false,
  },
  {
    id: "n2",
    kind: "success",
    title: "Batch OCR processing finished",
    description: "Job #989 parsed 2,048 medical claims with 99.6% field accuracy.",
    timestamp: "1h ago",
    href: "/jobs",
    read: false,
  },
  {
    id: "n3",
    kind: "processing",
    title: "Document classification in progress",
    description: "Job #992 is 31% complete — 45 shipping manifests remaining.",
    timestamp: "1h ago",
    href: "/jobs",
    read: false,
  },
  {
    id: "n4",
    kind: "error",
    title: "Layout parsing exception",
    description: "Purchase_Order_Scan_789.pdf failed validation — unreadable resolution.",
    timestamp: "3h ago",
    href: "/documents",
    read: true,
  },
  {
    id: "n5",
    kind: "system",
    title: "AI Provider failover triggered",
    description: "Primary GPU cluster latency elevated — traffic routed to OpenAI Azure Gateway.",
    timestamp: "5h ago",
    href: "/providers",
    read: true,
  },
  {
    id: "n6",
    kind: "success",
    title: "Audit summary report ready",
    description: "Monthly Field Extraction & Accuracy Report is ready to download.",
    timestamp: "Yesterday",
    href: "/reports",
    read: true,
  },
];

export const RECENT_ACTIVITY: ActivityEntry[] = [
  { id: "a1", actor: "You", action: "approved", target: "Commercial_Invoice_INV-8922.pdf", timestamp: "4m ago", href: "/documents/DOC-8922" },
  { id: "a2", actor: "Elena Vance", action: "ingested", target: "12 Insurance Claim PDFs", timestamp: "22m ago", href: "/documents" },
  { id: "a3", actor: "System Pipeline", action: "completed", target: "OCR Extraction Job #989", timestamp: "1h ago", href: "/jobs" },
  { id: "a4", actor: "Marcus Sterling", action: "rejected", target: "W2_Form_Scan_Invalid.jpg", timestamp: "2h ago", href: "/review" },
  { id: "a5", actor: "You", action: "rotated", target: "Production FastAPI Secret Key", timestamp: "Yesterday", href: "/settings#api" },
];
