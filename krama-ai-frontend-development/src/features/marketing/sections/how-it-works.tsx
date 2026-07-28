"use client";

import { motion } from "framer-motion";
import {
  UploadCloud,
  RefreshCw,
  ScanText,
  Tags,
  Sparkles,
  ShieldCheck,
  UserCheck,
  FilePieChart,
} from "lucide-react";
import { Section, SectionHeading, EASE } from "../components/section";

const STEPS = [
  { icon: UploadCloud, title: "Upload", detail: "Drag, drop, or stream via API" },
  { icon: ScanText, title: "OCR & AI Analysis", detail: "Ensemble text & layout recognition" },
  { icon: Tags, title: "Classification", detail: "Identify document type & schema" },
  { icon: Sparkles, title: "Extraction", detail: "Typed fields with confidence scores" },
  { icon: ShieldCheck, title: "Validation", detail: "Business rules & fraud checks" },
  { icon: UserCheck, title: "Human Review", detail: "Route edge cases to your team" },
  { icon: FilePieChart, title: "Decision & Reporting", detail: "Auto-adjudicate & export API" },
];

export function HowItWorksSection() {
  return (
    <Section id="how-it-works">
      <SectionHeading
        eyebrow="The pipeline"
        title={
          <>
            Eight stages. <span className="ai-gradient-text">One continuous flow.</span>
          </>
        }
        description="Every document travels the same deterministic path. You get observability at each hop and can branch, retry, or halt any stage through policy."
      />

      <div className="relative mt-16">
        {/* --------- Desktop: horizontal flow --------- */}
        <div className="hidden lg:block">
          {/* Connector track */}
          <div
            aria-hidden="true"
            className="absolute left-0 right-0 top-[30px] h-px bg-foreground/[0.08]"
          />
          {/* Animated energy pulse along the track */}
          <motion.div
            aria-hidden="true"
            className="absolute top-[29px] h-[3px] w-24 rounded-full"
            style={{
              background:
                "linear-gradient(90deg, transparent, hsl(190 95% 60%), hsl(262 90% 65%), transparent)",
              filter: "blur(0.5px)",
            }}
            animate={{ left: ["-10%", "100%"] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
          />

          <ol className="relative grid grid-cols-7 gap-2">
            {STEPS.map((step, i) => (
              <motion.li
                key={step.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.55, delay: i * 0.08, ease: EASE }}
                className="group flex flex-col items-center text-center"
              >
                {/* Node */}
                <div className="relative">
                  <motion.div
                    aria-hidden="true"
                    className="absolute inset-0 rounded-2xl ai-gradient-bg blur-md"
                    animate={{ opacity: [0.15, 0.4, 0.15] }}
                    transition={{
                      duration: 3.2,
                      repeat: Infinity,
                      delay: i * 0.35,
                      ease: "easeInOut",
                    }}
                  />
                  <div className="relative flex h-[60px] w-[60px] items-center justify-center rounded-2xl glass-strong transition-transform duration-500 group-hover:scale-105">
                    <step.icon className="h-5 w-5 text-foreground/80" />
                  </div>
                  <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-background text-[9px] font-semibold text-foreground/45 ring-1 ring-foreground/10">
                    {i + 1}
                  </span>
                </div>

                <h3 className="mt-4 text-[13px] font-semibold tracking-tight">
                  {step.title}
                </h3>
                <p className="mt-1 text-[11px] leading-snug text-foreground/45">
                  {step.detail}
                </p>
              </motion.li>
            ))}
          </ol>
        </div>

        {/* --------- Mobile / tablet: vertical flow --------- */}
        <ol className="relative space-y-1 lg:hidden">
          {/* Vertical track */}
          <div
            aria-hidden="true"
            className="absolute bottom-8 left-[29px] top-8 w-px bg-foreground/[0.08]"
          />
          <motion.div
            aria-hidden="true"
            className="absolute left-[28px] h-16 w-[3px] rounded-full"
            style={{
              background:
                "linear-gradient(180deg, transparent, hsl(190 95% 60%), hsl(262 90% 65%), transparent)",
            }}
            animate={{ top: ["2%", "94%"] }}
            transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
          />

          {STEPS.map((step, i) => (
            <motion.li
              key={step.title}
              initial={{ opacity: 0, x: -14 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.06, ease: EASE }}
              className="relative flex items-center gap-4 py-2"
            >
              <div className="relative shrink-0">
                <div
                  aria-hidden="true"
                  className="absolute inset-0 rounded-xl ai-gradient-bg opacity-25 blur-md"
                />
                <div className="relative flex h-[58px] w-[58px] items-center justify-center rounded-xl glass-strong">
                  <step.icon className="h-5 w-5 text-foreground/80" />
                </div>
                <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-background text-[9px] font-semibold text-foreground/45 ring-1 ring-foreground/10">
                  {i + 1}
                </span>
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold tracking-tight">{step.title}</h3>
                <p className="mt-0.5 text-xs text-foreground/45">{step.detail}</p>
              </div>
            </motion.li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
