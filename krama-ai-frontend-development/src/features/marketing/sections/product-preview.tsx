"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LayoutDashboard, UploadCloud, FileSearch, UserCheck, BarChart3 } from "lucide-react";
import { Section, SectionHeading, EASE } from "../components/section";
import {
  DashboardMockup,
  UploadMockup,
  ViewerMockup,
  ReviewMockup,
  AnalyticsMockup,
} from "../components/mockups";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "health", label: "Health Claims", icon: LayoutDashboard, Mock: DashboardMockup, blurb: "Process discharge summaries, hospital bills, pharmacy receipts, and lab reports." },
  { id: "motor", label: "Motor Claims", icon: UploadCloud, Mock: UploadMockup, blurb: "Extract data from police FIRs, repair estimates, and surveyor reports." },
  { id: "life", label: "Life Claims", icon: FileSearch, Mock: ViewerMockup, blurb: "Validate death certificates, nominee forms, and KYC compliance documents." },
  { id: "hospital", label: "Hospital Documents", icon: UserCheck, Mock: ReviewMockup, blurb: "Reconcile cashless authorization requests and TPA pre-auth forms." },
  { id: "policy", label: "Policy Documents", icon: BarChart3, Mock: AnalyticsMockup, blurb: "Verify claims against policy rules, waiting periods, and network hospital lists." },
] as const;

export function ProductPreviewSection() {
  const [active, setActive] = useState<string>(TABS[0].id);
  const current = TABS.find((t) => t.id === active) ?? TABS[0];
  const ActiveMock = current.Mock;

  return (
    <Section id="claim-types">
      <SectionHeading
        eyebrow="Claim Types"
        title={
          <>
            Every claim type,{" "}
            <span className="ai-gradient-text">every document</span>
          </>
        }
        description="From motor accidents to hospital cashless, we process every claim document Indian insurers handle through a unified workspace."
      />

      {/* Tab switcher */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: EASE }}
        className="mt-12 flex justify-center"
      >
        <div
          role="tablist"
          aria-label="Product screens"
          className="glass flex max-w-full gap-1 overflow-x-auto rounded-2xl p-1.5"
        >
          {TABS.map((tab) => {
            const isActive = tab.id === active;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => setActive(tab.id)}
                className={cn(
                  "relative flex shrink-0 items-center gap-2 rounded-xl px-3.5 py-2 text-[13px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  isActive ? "text-white" : "text-foreground/55 hover:text-foreground/85"
                )}
              >
                {isActive && (
                  <motion.span
                    layoutId="preview-tab"
                    className="absolute inset-0 rounded-xl ai-gradient-bg"
                    transition={{ type: "spring", stiffness: 320, damping: 32 }}
                  />
                )}
                <tab.icon className="relative z-10 h-3.5 w-3.5" />
                <span className="relative z-10 whitespace-nowrap">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Layered floating stage */}
      <div className="relative mt-12 [perspective:1600px]">
        {/* Ambient glow */}
        <div
          aria-hidden="true"
          className="absolute inset-x-8 -top-6 bottom-0 rounded-[40px] opacity-70 blur-3xl"
          style={{
            background:
              "radial-gradient(60% 60% at 50% 40%, hsl(262 90% 65% / 0.22), hsl(190 95% 60% / 0.08) 60%, transparent 80%)",
          }}
        />

        {/* Depth stack behind */}
        <div
          aria-hidden="true"
          className="absolute inset-x-16 -top-7 h-full rounded-2xl border border-foreground/[0.05] bg-foreground/[0.015]"
        />
        <div
          aria-hidden="true"
          className="absolute inset-x-8 -top-3.5 h-full rounded-2xl border border-foreground/[0.07] bg-foreground/[0.025]"
        />

        <motion.div
          animate={{ y: [0, -8, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          className="relative mx-auto max-w-4xl"
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={{ opacity: 0, y: 14, rotateX: 4 }}
              animate={{ opacity: 1, y: 0, rotateX: 0 }}
              exit={{ opacity: 0, y: -10, rotateX: -3 }}
              transition={{ duration: 0.45, ease: EASE }}
            >
              <ActiveMock />
            </motion.div>
          </AnimatePresence>
        </motion.div>

        {/* Caption */}
        <AnimatePresence mode="wait">
          <motion.p
            key={`${active}-blurb`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.35, ease: EASE }}
            className="relative mx-auto mt-8 max-w-xl text-center text-sm text-foreground/50"
          >
            {current.blurb}
          </motion.p>
        </AnimatePresence>
      </div>
    </Section>
  );
}
