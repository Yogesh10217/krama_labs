"use client";

import { motion } from "framer-motion";
import { Check, Minus, Gauge, Target, Workflow, Layers, ScrollText } from "lucide-react";
import { Section, SectionHeading, fadeUp, staggerContainer, EASE } from "../components/section";
import { AnimatedCounter } from "../components/animated-counter";

const COMPARISONS = [
  {
    icon: Gauge,
    dimension: "Speed",
    manual: "6–12 minutes per document, gated by analyst availability",
    krama: "Sub-second median page latency with unlimited parallelism",
    delta: { value: 23, suffix: " days", label: "cut from assessment" },
  },
  {
    icon: Target,
    dimension: "Cost Savings",
    manual: "Rising manual processing costs and overhead per claim",
    krama: "End-to-end automation of standard claims workflows",
    delta: { value: 82, suffix: "M", label: "saved by Aviva in 1 yr" },
  },
  {
    icon: Workflow,
    dimension: "Customer Satisfaction",
    manual: "Endless wait times lead to frustrated policyholders",
    krama: "Instant claims approval or clear reasons for manual review",
    delta: { value: 65, suffix: "%", label: "fewer complaints" },
  },
  {
    icon: Layers,
    dimension: "ROI for AI Leaders",
    manual: "Lagging peers struggle with legacy operating costs",
    krama: "AI-native insurers vastly outperform traditional players",
    delta: { value: 6.1, decimals: 1, suffix: "×", label: "shareholder returns" },
  },
  {
    icon: ScrollText,
    dimension: "Compliance",
    manual: "Fragmented email trails and unverifiable manual sign-offs",
    krama: "Immutable audit logs, retention policies, and exportable evidence",
    delta: { value: 100, suffix: "%", label: "actions audited" },
  },
];

export function WhyKramaSection() {
  return (
    <Section id="why">
      <SectionHeading
        eyebrow="McKinsey Validated"
        title={
          <>
            The data says <span className="ai-gradient-text">it all</span>
          </>
        }
        description="McKinsey's July 2025 report confirms: Insurers that merely dabble in AI risk being left in the dust. See the real-world impact of AI claims processing vs manual workflows."
      />

      <motion.ul
        variants={staggerContainer}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        className="mt-14 space-y-3"
      >
        {COMPARISONS.map((row) => (
          <motion.li key={row.dimension} variants={fadeUp}>
            <article className="group glass lift relative overflow-hidden rounded-2xl">
              <div className="grid grid-cols-1 items-stretch md:grid-cols-[200px_1fr_1fr_150px]">
                {/* Dimension */}
                <div className="flex items-center gap-3 border-foreground/[0.07] p-5 md:border-r">
                  <div className="relative shrink-0">
                    <div
                      aria-hidden="true"
                      className="absolute inset-0 rounded-lg ai-gradient-bg opacity-25 blur-md transition-opacity duration-500 group-hover:opacity-50"
                    />
                    <div className="relative flex h-9 w-9 items-center justify-center rounded-lg glass">
                      <row.icon className="h-4 w-4 text-foreground/80" />
                    </div>
                  </div>
                  <h3 className="text-[15px] font-semibold tracking-tight">
                    {row.dimension}
                  </h3>
                </div>

                {/* Manual */}
                <div className="flex items-start gap-2.5 border-foreground/[0.07] p-5 md:border-r">
                  <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-foreground/[0.07]">
                    <Minus className="h-2.5 w-2.5 text-foreground/40" />
                  </span>
                  <div>
                    <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-foreground/35">
                      Manual process
                    </p>
                    <p className="text-[13px] leading-relaxed text-foreground/50">
                      {row.manual}
                    </p>
                  </div>
                </div>

                {/* Krama */}
                <div className="flex items-start gap-2.5 border-foreground/[0.07] p-5 md:border-r">
                  <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/15">
                    <Check className="h-2.5 w-2.5 text-emerald-400" />
                  </span>
                  <div>
                    <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-primary/70">
                      With Krama AI
                    </p>
                    <p className="text-[13px] leading-relaxed text-foreground/75">
                      {row.krama}
                    </p>
                  </div>
                </div>

                {/* Delta */}
                <div className="flex flex-col justify-center bg-foreground/[0.02] p-5 text-center">
                  <span className="text-2xl font-semibold tracking-tight ai-gradient-text">
                    <AnimatedCounter value={row.delta.value} suffix={row.delta.suffix} />
                  </span>
                  <span className="mt-1 text-[10px] uppercase tracking-wider text-foreground/35">
                    {row.delta.label}
                  </span>
                </div>
              </div>

              {/* Reveal hairline */}
              <motion.div
                aria-hidden="true"
                className="pointer-events-none absolute inset-x-0 bottom-0 h-px opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                style={{
                  background:
                    "linear-gradient(90deg, transparent, hsl(262 90% 65% / 0.6), transparent)",
                }}
                transition={{ duration: 0.4, ease: EASE }}
              />
            </article>
          </motion.li>
        ))}
      </motion.ul>
    </Section>
  );
}
