"use client";

import { motion } from "framer-motion";
import {
  BrainCircuit,
  LayoutDashboard,
  Files,
  UploadCloud,
  UserCheck,
  BarChart3,
  Search,
  CheckCircle2,
  FileText,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { EASE } from "./section";

/* ------------------------------------------------------------------ *
 * Shared chrome — a glass "app window" frame used by every mockup.
 * ------------------------------------------------------------------ */

export function AppWindow({
  children,
  label,
  className,
}: {
  children: React.ReactNode;
  label: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl glass-strong gradient-border",
        className
      )}
      role="img"
      aria-label={`${label} interface preview`}
    >
      {/* Title bar */}
      <div className="flex h-9 items-center gap-2 border-b border-foreground/[0.06] px-3.5">
        <span className="h-2.5 w-2.5 rounded-full bg-foreground/15" />
        <span className="h-2.5 w-2.5 rounded-full bg-foreground/15" />
        <span className="h-2.5 w-2.5 rounded-full bg-foreground/15" />
        <div className="ml-2 flex items-center gap-1.5 rounded-md bg-foreground/[0.04] px-2 py-0.5">
          <span className="h-1.5 w-1.5 rounded-full bg-[hsl(190_95%_60%)]" />
          <span className="text-[9px] font-medium tracking-wide text-foreground/45">
            krama.ai/{label.toLowerCase().replace(/\s+/g, "-")}
          </span>
        </div>
      </div>
      {children}
    </div>
  );
}

/** Tiny sidebar rail shared by the mockups. */
function MiniRail({ active = 0 }: { active?: number }) {
  const icons = [LayoutDashboard, Files, UploadCloud, UserCheck, BarChart3];
  return (
    <div className="hidden w-11 shrink-0 flex-col items-center gap-1.5 border-r border-foreground/[0.06] py-3 sm:flex">
      <div className="mb-2 rounded-md bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)] p-1">
        <BrainCircuit className="h-3 w-3 text-white" />
      </div>
      {icons.map((Icon, i) => (
        <div
          key={i}
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-md transition-colors",
            i === active ? "ai-gradient-bg text-white" : "text-foreground/25"
          )}
        >
          <Icon className="h-3 w-3" />
        </div>
      ))}
    </div>
  );
}

/** Animated bar chart used across mockups. */
function MiniBars({ bars }: { bars: number[] }) {
  return (
    <div className="flex h-full items-end gap-1.5">
      {bars.map((h, i) => (
        <motion.div
          key={i}
          className="flex-1 rounded-t-[3px]"
          style={{
            background:
              i === bars.length - 2
                ? "linear-gradient(180deg, hsl(190 95% 60%), hsl(262 90% 65%))"
                : "hsl(var(--foreground) / 0.12)",
          }}
          initial={{ height: 0 }}
          whileInView={{ height: `${h}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay: 0.25 + i * 0.05, ease: EASE }}
        />
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * 1. Dashboard
 * ------------------------------------------------------------------ */

export function DashboardMockup() {
  const kpis = [
    { label: "Processed", value: "142,394" },
    { label: "Accuracy", value: "99.4%" },
    { label: "Queue", value: "169" },
  ];

  return (
    <AppWindow label="Dashboard">
      <div className="flex">
        <MiniRail active={0} />
        <div className="flex-1 space-y-3 p-3.5">
          {/* Header row */}
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="h-2 w-24 rounded-full bg-foreground/20" />
              <div className="h-1.5 w-32 rounded-full bg-foreground/10" />
            </div>
            <div className="flex items-center gap-1 rounded-md ai-gradient-bg px-2 py-1">
              <UploadCloud className="h-2.5 w-2.5 text-white" />
              <span className="text-[8px] font-medium text-white">Upload</span>
            </div>
          </div>

          {/* KPI tiles */}
          <div className="grid grid-cols-3 gap-2">
            {kpis.map((kpi, i) => (
              <motion.div
                key={kpi.label}
                className="glass rounded-lg p-2"
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.15 + i * 0.08, ease: EASE }}
              >
                <div className="mb-1 h-1 w-8 rounded-full bg-foreground/15" />
                <div className="text-[11px] font-semibold tracking-tight text-foreground/85">
                  {kpi.value}
                </div>
                <div className="text-[7px] uppercase tracking-wider text-foreground/35">
                  {kpi.label}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Chart + side list */}
          <div className="grid grid-cols-5 gap-2">
            <div className="col-span-3 glass rounded-lg p-2.5">
              <div className="mb-2 h-1.5 w-16 rounded-full bg-foreground/15" />
              <div className="h-16">
                <MiniBars bars={[38, 55, 42, 68, 50, 82, 64]} />
              </div>
            </div>
            <div className="col-span-2 glass space-y-1.5 rounded-lg p-2.5">
              <div className="mb-1 h-1.5 w-12 rounded-full bg-foreground/15" />
              {[0, 1, 2, 3].map((i) => (
                <motion.div
                  key={i}
                  className="flex items-center gap-1.5"
                  initial={{ opacity: 0, x: -6 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.4 + i * 0.09, ease: EASE }}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 shrink-0 rounded-full",
                      i === 2 ? "bg-amber-400" : "bg-emerald-400"
                    )}
                  />
                  <span className="h-1 flex-1 rounded-full bg-foreground/10" />
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

/* ------------------------------------------------------------------ *
 * 2. Upload
 * ------------------------------------------------------------------ */

export function UploadMockup() {
  const files = [
    { name: "Q4_Financial_Report.pdf", pct: 100, done: true },
    { name: "MSA_TechCorp_Signed.docx", pct: 72, done: false },
    { name: "Invoice_INV-0042.jpg", pct: 34, done: false },
  ];

  return (
    <AppWindow label="Upload">
      <div className="flex">
        <MiniRail active={2} />
        <div className="flex-1 space-y-2.5 p-3.5">
          {/* Dropzone */}
          <motion.div
            className="relative flex flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed border-foreground/15 py-5"
            animate={{
              borderColor: [
                "hsl(var(--foreground) / 0.15)",
                "hsl(262 90% 65% / 0.5)",
                "hsl(var(--foreground) / 0.15)",
              ],
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <motion.div
              className="rounded-full ai-gradient-bg p-1.5"
              animate={{ y: [0, -3, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <UploadCloud className="h-3 w-3 text-white" />
            </motion.div>
            <div className="h-1.5 w-28 rounded-full bg-foreground/15" />
            <div className="h-1 w-20 rounded-full bg-foreground/8" />
          </motion.div>

          {/* Queue */}
          <div className="space-y-1.5">
            {files.map((f, i) => (
              <div key={f.name} className="glass rounded-lg p-2">
                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-1.5">
                    <FileText className="h-2.5 w-2.5 shrink-0 text-foreground/40" />
                    <span className="truncate text-[8px] text-foreground/60">
                      {f.name}
                    </span>
                  </div>
                  {f.done ? (
                    <CheckCircle2 className="h-2.5 w-2.5 shrink-0 text-emerald-400" />
                  ) : (
                    <span className="shrink-0 text-[7px] font-mono text-foreground/40">
                      {f.pct}%
                    </span>
                  )}
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-foreground/8">
                  <motion.div
                    className="h-full rounded-full"
                    style={{
                      background: f.done
                        ? "hsl(152 70% 45%)"
                        : "linear-gradient(90deg, hsl(190 95% 60%), hsl(262 90% 65%))",
                    }}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${f.pct}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.1, delay: 0.3 + i * 0.15, ease: EASE }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

/* ------------------------------------------------------------------ *
 * 3. Document Viewer (OCR overlay)
 * ------------------------------------------------------------------ */

export function ViewerMockup() {
  const boxes = [
    { top: "18%", left: "12%", w: "44%", tone: "emerald" },
    { top: "32%", left: "12%", w: "28%", tone: "emerald" },
    { top: "58%", left: "48%", w: "34%", tone: "amber" },
    { top: "72%", left: "48%", w: "26%", tone: "rose" },
  ];

  const fields = [
    { label: "Invoice No.", conf: 98, tone: "emerald" },
    { label: "Vendor", conf: 94, tone: "emerald" },
    { label: "Tax Amount", conf: 68, tone: "amber" },
    { label: "Total", conf: 45, tone: "rose" },
  ];

  const toneMap: Record<string, string> = {
    emerald: "hsl(152 70% 50%)",
    amber: "hsl(38 92% 55%)",
    rose: "hsl(350 85% 60%)",
  };

  return (
    <AppWindow label="Document Viewer">
      <div className="grid grid-cols-5">
        {/* Page canvas */}
        <div className="relative col-span-3 min-h-[190px] border-r border-foreground/[0.06] bg-foreground/[0.03] p-3">
          <div className="relative h-full w-full rounded-md bg-foreground/[0.05] p-3">
            <div className="space-y-1.5">
              <div className="h-2.5 w-16 rounded bg-foreground/20" />
              <div className="h-1 w-24 rounded bg-foreground/10" />
              <div className="h-1 w-20 rounded bg-foreground/10" />
            </div>
            {boxes.map((b, i) => (
              <motion.div
                key={i}
                className="absolute rounded-[3px] border"
                style={{
                  top: b.top,
                  left: b.left,
                  width: b.w,
                  height: "9%",
                  borderColor: toneMap[b.tone],
                  background: `color-mix(in oklab, ${toneMap[b.tone]} 14%, transparent)`,
                }}
                initial={{ opacity: 0, scale: 0.94 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: 0.3 + i * 0.12, ease: EASE }}
              />
            ))}
            {/* Scanning sweep */}
            <motion.div
              className="pointer-events-none absolute inset-x-0 h-8"
              style={{
                background:
                  "linear-gradient(180deg, transparent, hsl(190 95% 60% / 0.18), transparent)",
              }}
              animate={{ top: ["0%", "88%", "0%"] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            />
          </div>
        </div>

        {/* Field inspector */}
        <div className="col-span-2 space-y-2 p-3">
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-2.5 w-2.5 text-primary" />
            <div className="h-1.5 w-14 rounded-full bg-foreground/18" />
          </div>
          {fields.map((f, i) => (
            <motion.div
              key={f.label}
              className="space-y-1"
              initial={{ opacity: 0, x: 8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: 0.35 + i * 0.1, ease: EASE }}
            >
              <div className="flex items-center justify-between">
                <span className="text-[7px] uppercase tracking-wider text-foreground/40">
                  {f.label}
                </span>
                <span
                  className="font-mono text-[7px]"
                  style={{ color: toneMap[f.tone] }}
                >
                  {f.conf}%
                </span>
              </div>
              <div
                className="h-4 rounded border"
                style={{
                  borderColor: `color-mix(in oklab, ${toneMap[f.tone]} 35%, transparent)`,
                  background: `color-mix(in oklab, ${toneMap[f.tone]} 7%, transparent)`,
                }}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </AppWindow>
  );
}

/* ------------------------------------------------------------------ *
 * 4. Human Review
 * ------------------------------------------------------------------ */

export function ReviewMockup() {
  const rows = [
    { conf: "74%", tone: "amber", pri: "High" },
    { conf: "68%", tone: "amber", pri: "Med" },
    { conf: "45%", tone: "rose", pri: "High" },
    { conf: "81%", tone: "emerald", pri: "Low" },
  ];
  const toneMap: Record<string, string> = {
    emerald: "hsl(152 70% 50%)",
    amber: "hsl(38 92% 55%)",
    rose: "hsl(350 85% 60%)",
  };

  return (
    <AppWindow label="Human Review">
      <div className="flex">
        <MiniRail active={3} />
        <div className="flex-1 space-y-2.5 p-3.5">
          <div className="flex items-center justify-between">
            <div className="h-2 w-20 rounded-full bg-foreground/20" />
            <div className="flex gap-1">
              <div className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[7px] font-medium text-emerald-400">
                Approve
              </div>
              <div className="rounded bg-foreground/8 px-1.5 py-0.5 text-[7px] font-medium text-foreground/50">
                Reject
              </div>
            </div>
          </div>

          {/* Search bar */}
          <div className="flex items-center gap-1.5 rounded-md bg-foreground/[0.05] px-2 py-1.5">
            <Search className="h-2.5 w-2.5 text-foreground/30" />
            <div className="h-1 w-20 rounded-full bg-foreground/10" />
          </div>

          {/* Table */}
          <div className="space-y-1">
            {rows.map((r, i) => (
              <motion.div
                key={i}
                className="flex items-center gap-2 rounded-md px-1.5 py-1.5 transition-colors hover:bg-foreground/[0.04]"
                initial={{ opacity: 0, y: 6 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.25 + i * 0.09, ease: EASE }}
              >
                <div className="h-4 w-4 shrink-0 rounded bg-foreground/8" />
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="h-1.5 w-3/4 rounded-full bg-foreground/15" />
                  <div className="h-1 w-1/3 rounded-full bg-foreground/8" />
                </div>
                <span
                  className="shrink-0 rounded px-1 py-0.5 font-mono text-[7px]"
                  style={{
                    color: toneMap[r.tone],
                    background: `color-mix(in oklab, ${toneMap[r.tone]} 12%, transparent)`,
                  }}
                >
                  {r.conf}
                </span>
                <span className="w-6 shrink-0 text-right text-[7px] text-foreground/35">
                  {r.pri}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </AppWindow>
  );
}

/* ------------------------------------------------------------------ *
 * 5. Analytics
 * ------------------------------------------------------------------ */

export function AnalyticsMockup() {
  return (
    <AppWindow label="Analytics">
      <div className="flex">
        <MiniRail active={4} />
        <div className="flex-1 space-y-3 p-3.5">
          <div className="flex items-center justify-between">
            <div className="h-2 w-16 rounded-full bg-foreground/20" />
            <div className="flex gap-1">
              {["7d", "30d", "90d"].map((t, i) => (
                <span
                  key={t}
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[7px]",
                    i === 1
                      ? "ai-gradient-bg text-white"
                      : "bg-foreground/[0.05] text-foreground/40"
                  )}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Area chart */}
          <div className="glass relative h-20 overflow-hidden rounded-lg p-2">
            <svg viewBox="0 0 200 60" className="h-full w-full" preserveAspectRatio="none">
              <defs>
                <linearGradient id="mkArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(262 90% 65%)" stopOpacity="0.45" />
                  <stop offset="100%" stopColor="hsl(262 90% 65%)" stopOpacity="0" />
                </linearGradient>
              </defs>
              <motion.path
                d="M0,46 C20,40 30,22 50,26 C70,30 80,14 100,18 C120,22 130,8 150,12 C170,16 185,6 200,10 L200,60 L0,60 Z"
                fill="url(#mkArea)"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.5 }}
              />
              <motion.path
                d="M0,46 C20,40 30,22 50,26 C70,30 80,14 100,18 C120,22 130,8 150,12 C170,16 185,6 200,10"
                fill="none"
                stroke="hsl(262 90% 70%)"
                strokeWidth="1.6"
                strokeLinecap="round"
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1.5, delay: 0.25, ease: EASE }}
              />
            </svg>
          </div>

          {/* Donut + legend */}
          <div className="grid grid-cols-5 gap-2">
            <div className="col-span-2 glass flex items-center justify-center rounded-lg p-2">
              <svg viewBox="0 0 42 42" className="h-14 w-14 -rotate-90">
                {[
                  { c: "hsl(190 95% 60%)", d: 45, o: 0 },
                  { c: "hsl(262 90% 65%)", d: 30, o: 45 },
                  { c: "hsl(320 90% 65%)", d: 15, o: 75 },
                  { c: "hsl(var(--foreground) / 0.12)", d: 10, o: 90 },
                ].map((s, i) => (
                  <motion.circle
                    key={i}
                    cx="21"
                    cy="21"
                    r="15.5"
                    fill="none"
                    stroke={s.c}
                    strokeWidth="6"
                    strokeDasharray={`${s.d} ${100 - s.d}`}
                    strokeDashoffset={-s.o}
                    pathLength={100}
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }}
                  />
                ))}
              </svg>
            </div>
            <div className="col-span-3 glass space-y-1.5 rounded-lg p-2.5">
              {[
                "hsl(190 95% 60%)",
                "hsl(262 90% 65%)",
                "hsl(320 90% 65%)",
              ].map((c, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span
                    className="h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{ background: c }}
                  />
                  <span className="h-1 flex-1 rounded-full bg-foreground/10" />
                  <span className="h-1 w-5 rounded-full bg-foreground/15" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppWindow>
  );
}
