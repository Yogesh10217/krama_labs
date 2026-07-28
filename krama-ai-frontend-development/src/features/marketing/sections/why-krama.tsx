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
    delta: { value: 340, suffix: "×", label: "faster throughput" },
  },
  {
    icon: Target,
    dimension: "Accuracy",
    manual: "4–8% keying error rate that compounds downstream",
    krama: "99.4% field accuracy with confidence-routed exception handling",
    delta: { value: 96, suffix: "%", label: "fewer errors" },
  },
  {
    icon: Workflow,
    dimension: "Automation",
    manual: "Copy-paste between inboxes, spreadsheets, and line-of-business apps",
    krama: "Policy-driven pipelines with webhooks into your existing systems",
    delta: { value: 92, suffix: "%", label: "touchless processing" },
  },
  {
    icon: Layers,
    dimension: "Scalability",
    manual: "Linear headcount growth to absorb seasonal volume spikes",
    krama: "Elastic GPU capacity that absorbs 10× spikes without hiring",
    delta: { value: 10, suffix: "×", label: "burst capacity" },
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
        eyebrow="Why Krama AI"
        title={
          <>
            Manual processing doesn&apos;t scale.{" "}
            <span className="ai-gradient-text">Intelligence does.</span>
          </>
        }
        description="A side-by-side look at what changes when document operations move from human keying to an AI-native pipeline with humans in the loop only where they add value."
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
