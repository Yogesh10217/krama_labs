"use client";

import { motion } from "framer-motion";
import {
  ScanText,
  Sparkles,
  UserCheck,
  BarChart3,
  FilePieChart,
  Workflow,
  Network,
  Lock,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Section, SectionHeading, fadeUp, staggerContainer, EASE } from "../components/section";

/* ------------------------------------------------------------------ *
 * Micro-illustrations — tiny SVG/DOM sketches, one per feature.
 * They reuse palette tokens so nothing new is introduced.
 * ------------------------------------------------------------------ */

function IllusScan() {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg bg-foreground/[0.03] p-2.5">
      <div className="space-y-1.5">
        {[80, 62, 71, 45].map((w, i) => (
          <div key={i} className="h-1.5 rounded-full bg-foreground/12" style={{ width: `${w}%` }} />
        ))}
      </div>
      <motion.div
        className="absolute inset-x-0 h-6"
        style={{
          background:
            "linear-gradient(180deg, transparent, hsl(190 95% 60% / 0.28), transparent)",
        }}
        animate={{ top: ["-10%", "100%"] }}
        transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}

function IllusExtract() {
  return (
    <div className="flex h-full w-full items-center gap-2 rounded-lg bg-foreground/[0.03] p-2.5">
      <div className="flex-1 space-y-1">
        {[70, 50, 60].map((w, i) => (
          <div key={i} className="h-1.5 rounded-full bg-foreground/12" style={{ width: `${w}%` }} />
        ))}
      </div>
      <motion.div
        animate={{ x: [0, 3, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="text-foreground/25"
      >
        →
      </motion.div>
      <div className="flex-1 space-y-1">
        {["hsl(190 95% 60%)", "hsl(262 90% 65%)", "hsl(320 90% 65%)"].map((c, i) => (
          <motion.div
            key={i}
            className="h-1.5 rounded-full"
            style={{ background: c, opacity: 0.75 }}
            initial={{ width: 0 }}
            whileInView={{ width: `${70 - i * 12}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: 0.2 + i * 0.12, ease: EASE }}
          />
        ))}
      </div>
    </div>
  );
}

function IllusReview() {
  return (
    <div className="flex h-full w-full flex-col justify-center gap-1.5 rounded-lg bg-foreground/[0.03] p-2.5">
      {[
        { c: "hsl(152 70% 50%)", w: 78 },
        { c: "hsl(38 92% 55%)", w: 58 },
        { c: "hsl(350 85% 60%)", w: 66 },
      ].map((r, i) => (
        <motion.div
          key={i}
          className="flex items-center gap-2"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 3, repeat: Infinity, delay: i * 0.5, ease: "easeInOut" }}
        >
          <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: r.c }} />
          <span className="h-1.5 rounded-full bg-foreground/12" style={{ width: `${r.w}%` }} />
        </motion.div>
      ))}
    </div>
  );
}

function IllusAnalytics() {
  return (
    <div className="flex h-full w-full items-end gap-1.5 rounded-lg bg-foreground/[0.03] p-2.5">
      {[35, 58, 44, 72, 52, 88].map((h, i) => (
        <motion.div
          key={i}
          className="flex-1 rounded-t-[3px]"
          style={{
            background:
              i === 5
                ? "linear-gradient(180deg, hsl(190 95% 60%), hsl(262 90% 65%))"
                : "hsl(var(--foreground) / 0.12)",
          }}
          initial={{ height: 0 }}
          whileInView={{ height: `${h}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.15 + i * 0.06, ease: EASE }}
        />
      ))}
    </div>
  );
}

function IllusReports() {
  return (
    <div className="relative h-full w-full rounded-lg bg-foreground/[0.03] p-2.5">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute rounded-md border border-foreground/10 bg-background/60"
          style={{
            inset: `${10 + i * 5}px ${14 + i * 7}px ${10 - i * 2}px ${10 + i * 7}px`,
            zIndex: 3 - i,
          }}
          animate={{ y: [0, -2 - i, 0] }}
          transition={{ duration: 4 + i, repeat: Infinity, ease: "easeInOut", delay: i * 0.3 }}
        >
          {i === 0 && (
            <div className="space-y-1 p-2">
              <div className="h-1 w-8 rounded-full ai-gradient-bg opacity-70" />
              <div className="h-1 w-12 rounded-full bg-foreground/12" />
              <div className="h-1 w-9 rounded-full bg-foreground/12" />
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
}

function IllusWorkflow() {
  return (
    <div className="flex h-full w-full items-center justify-between rounded-lg bg-foreground/[0.03] px-3">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="flex items-center">
          <motion.span
            className="h-2.5 w-2.5 rounded-full"
            style={{
              background:
                i === 3 ? "hsl(320 90% 65%)" : i === 0 ? "hsl(190 95% 60%)" : "hsl(262 90% 65%)",
            }}
            animate={{ scale: [1, 1.35, 1], opacity: [0.55, 1, 0.55] }}
            transition={{ duration: 2.2, repeat: Infinity, delay: i * 0.45, ease: "easeInOut" }}
          />
          {i < 3 && <span className="mx-1 h-px w-5 bg-foreground/12 sm:w-7" />}
        </div>
      ))}
    </div>
  );
}

function IllusProviders() {
  return (
    <div className="relative flex h-full w-full items-center justify-center rounded-lg bg-foreground/[0.03]">
      <span className="absolute h-6 w-6 rounded-lg ai-gradient-bg opacity-80" />
      {[0, 1, 2, 3].map((i) => (
        <motion.span
          key={i}
          className="absolute h-1.5 w-1.5 rounded-full bg-foreground/35"
          style={{
            transform: `rotate(${i * 90}deg) translateX(28px)`,
          }}
          animate={{ opacity: [0.25, 0.9, 0.25] }}
          transition={{ duration: 2.4, repeat: Infinity, delay: i * 0.35, ease: "easeInOut" }}
        />
      ))}
      <motion.span
        className="absolute h-14 w-14 rounded-full border border-dashed border-foreground/12"
        animate={{ rotate: 360 }}
        transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}

function IllusSecurity() {
  return (
    <div className="flex h-full w-full items-center justify-center rounded-lg bg-foreground/[0.03]">
      <motion.div
        className="relative"
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="absolute inset-0 rounded-lg ai-gradient-bg opacity-35 blur-md" />
        <div className="relative flex h-9 w-9 items-center justify-center rounded-lg glass">
          <Lock className="h-4 w-4 text-foreground/70" />
        </div>
      </motion.div>
    </div>
  );
}

/* ------------------------------------------------------------------ */

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
  illustration: () => React.JSX.Element;
  span?: boolean;
}

const FEATURES: Feature[] = [
  {
    icon: ScanText,
    title: "AI Vision OCR",
    description:
      "Reads printed text, handwriting, stamps, and signatures from any Indian document format with per-character confidence.",
    illustration: IllusScan,
    span: true,
  },
  {
    icon: Sparkles,
    title: "Field Extraction",
    description:
      "Schema-aware extraction and layout analysis that turns unstructured discharge summaries and bills into typed JSON.",
    illustration: IllusExtract,
    span: true,
  },
  {
    icon: UserCheck,
    title: "Human Review",
    description:
      "Confidence-routed review queues with side-by-side OCR overlays and full version history for edge cases.",
    illustration: IllusReview,
  },
  {
    icon: BarChart3,
    title: "Analytics",
    description:
      "Executive dashboards for claim volumes, accuracy, cost, and provider performance across every tenant.",
    illustration: IllusAnalytics,
  },
  {
    icon: FilePieChart,
    title: "Enterprise Reporting",
    description:
      "Scheduled PDF and CSV reporting for IRDAI SLA compliance delivered to stakeholders automatically.",
    illustration: IllusReports,
  },
  {
    icon: Workflow,
    title: "Validation Engine",
    description:
      "Cross-verify claims against policy rules, waiting periods, sub-limits, and network hospital lists.",
    illustration: IllusWorkflow,
  },
  {
    icon: Network,
    title: "Provider Management",
    description:
      "Route inference across OpenAI, Anthropic, Google, or private GPU clusters with weighted failover.",
    illustration: IllusProviders,
  },
  {
    icon: Lock,
    title: "Security & RBAC",
    description:
      "Isolated multi-tenant architecture with granular RBAC, customer-managed keys, and immutable audit logs.",
    illustration: IllusSecurity,
  },
];

export function FeaturesSection() {
  return (
    <Section id="features">
      <SectionHeading
        eyebrow="Platform capabilities"
        title={
          <>
            Everything you need to automate{" "}
            <span className="ai-gradient-text">insurance claims</span>
          </>
        }
        description="A complete pipeline — from raw upload to validated, auditable output — delivered as one coherent platform instead of a stack of point tools."
      />

      <motion.ul
        variants={staggerContainer}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {FEATURES.map((feature) => {
          const Illustration = feature.illustration;
          return (
            <motion.li
              key={feature.title}
              variants={fadeUp}
              className={feature.span ? "sm:col-span-2" : undefined}
            >
              <article className="group glass lift relative flex h-full flex-col overflow-hidden rounded-2xl p-5">
                {/* Gradient hairline that reveals on hover */}
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-x-0 top-0 h-px opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                  style={{
                    background:
                      "linear-gradient(90deg, transparent, hsl(262 90% 65% / 0.7), transparent)",
                  }}
                />

                {/* Illustration */}
                <div className="mb-5 h-[88px] w-full">
                  <Illustration />
                </div>

                <div className="flex items-center gap-2.5">
                  <div className="relative inline-flex shrink-0">
                    <div
                      aria-hidden="true"
                      className="absolute inset-0 rounded-lg ai-gradient-bg opacity-0 blur-md transition-opacity duration-500 group-hover:opacity-45"
                    />
                    <div className="relative flex h-8 w-8 items-center justify-center rounded-lg glass">
                      <feature.icon className="h-4 w-4 text-foreground/80" />
                    </div>
                  </div>
                  <h3 className="text-sm font-semibold tracking-tight">{feature.title}</h3>
                </div>

                <p className="mt-2.5 text-[13px] leading-relaxed text-foreground/55">
                  {feature.description}
                </p>
              </article>
            </motion.li>
          );
        })}
      </motion.ul>
    </Section>
  );
}
