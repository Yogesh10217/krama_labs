"use client";

import { motion } from "framer-motion";
import {
  Clock,
  RefreshCw,
  Files,
  AlertTriangle,
  Link2Off,
  ShieldAlert,
} from "lucide-react";
import { Section, SectionHeading, fadeUp, staggerContainer } from "../components/section";
import { AnimatedCounter } from "../components/animated-counter";

type Pillar = {
  icon: any;
  title: string;
  description: string;
  metric: { value: number; decimals?: number; suffix: string; label: string };
};

const PILLARS: Pillar[] = [
  {
    icon: Clock,
    title: "Long Processing Times",
    description:
      "Claim filed? Now wait 2-3 weeks for surveyors, document verification, and approvals. Meanwhile, the customer waits.",
    metric: { value: 14, suffix: "+", label: "Days delay" },
  },
  {
    icon: RefreshCw,
    title: "Endless Touchpoints",
    description:
      "Surveyor visits the garage. TPA calls for missing documents. Insurer asks for more photos. Every step is another delay.",
    metric: { value: 6, suffix: "", label: "Manual handoffs" },
  },
  {
    icon: Files,
    title: "Lost in Paperwork",
    description:
      "Discharge summaries, police FIRs, repair estimates, original bills... one missing document and you're back to square one.",
    metric: { value: 40, suffix: "+", label: "Pages per claim" },
  },
  {
    icon: AlertTriangle,
    title: "Undetected Fraud",
    description:
      "Forged documents, inflated bills, phantom claims — manual review can't catch what AI can see in seconds.",
    metric: { value: 8000, suffix: " Cr", label: "Lost to fraud" },
  },
  {
    icon: Link2Off,
    title: "Disconnected Systems",
    description:
      "Core systems, TPA portals, and surveyor apps don't talk. Teams spend hours manually re-keying data between screens.",
    metric: { value: 4, suffix: "", label: "Siloed platforms" },
  },
  {
    icon: ShieldAlert,
    title: "Compliance Challenges",
    description:
      "IRDAI SLA deadlines missed due to backlog. Inconsistent policy rule application leads to regulatory fines and warnings.",
    metric: { value: 100, suffix: "%", label: "Audit risk" },
  },
];

export function TrustSection() {
  return (
    <Section id="trust">
      <SectionHeading
        eyebrow="The Bottleneck"
        title={
          <>
            Every claim is stuck waiting{" "}
            <span className="ai-gradient-text">for someone to read it</span>
          </>
        }
        description="While AI writes code, creates art, and drives cars, your claims team is still manually reading discharge summaries. That's the gap we're closing."
      />

      <motion.ul
        variants={staggerContainer}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        {PILLARS.map((pillar) => (
          <motion.li key={pillar.title} variants={fadeUp}>
            <article className="group glass lift relative h-full overflow-hidden rounded-2xl p-6">
              {/* Hover aura */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-700 group-hover:opacity-100"
                style={{
                  background:
                    "radial-gradient(420px circle at 50% 0%, hsl(262 90% 65% / 0.1), transparent 65%)",
                }}
              />

              <div className="relative">
                <div className="relative mb-5 inline-flex">
                  <div
                    aria-hidden="true"
                    className="absolute inset-0 rounded-xl ai-gradient-bg opacity-25 blur-md transition-opacity duration-500 group-hover:opacity-50"
                  />
                  <div className="relative flex h-11 w-11 items-center justify-center rounded-xl glass">
                    <pillar.icon className="h-[18px] w-[18px] text-foreground/85" />
                  </div>
                </div>

                <h3 className="text-[15px] font-semibold tracking-tight">
                  {pillar.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-foreground/55">
                  {pillar.description}
                </p>

                <div className="mt-5 flex items-baseline gap-2 border-t border-foreground/[0.07] pt-4">
                  <span className="text-lg font-semibold tracking-tight ai-gradient-text">
                    <AnimatedCounter
                      value={pillar.metric.value}
                      decimals={pillar.metric.decimals ?? 0}
                      suffix={pillar.metric.suffix}
                    />
                  </span>
                  <span className="text-[11px] uppercase tracking-wider text-foreground/35">
                    {pillar.metric.label}
                  </span>
                </div>
              </div>
            </article>
          </motion.li>
        ))}
      </motion.ul>
    </Section>
  );
}
