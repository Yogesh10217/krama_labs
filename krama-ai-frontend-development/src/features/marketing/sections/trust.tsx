"use client";

import { motion } from "framer-motion";
import {
  ShieldCheck,
  Zap,
  Target,
  Building2,
  Network,
  ScrollText,
} from "lucide-react";
import { Section, SectionHeading, fadeUp, staggerContainer } from "../components/section";
import { AnimatedCounter } from "../components/animated-counter";

const PILLARS = [
  {
    icon: ShieldCheck,
    title: "Security",
    description:
      "SOC 2 Type II, ISO 27001, and GDPR aligned. AES-256 at rest, TLS 1.3 in transit, with customer-managed keys.",
    metric: { value: 256, suffix: "-bit", label: "AES encryption" },
  },
  {
    icon: Zap,
    title: "Fast Processing",
    description:
      "Distributed GPU inference with intelligent batching keeps median page latency under a second at any volume.",
    metric: { value: 0.8, decimals: 1, suffix: "s", label: "Median page latency" },
  },
  {
    icon: Target,
    title: "AI Accuracy",
    description:
      "Ensemble OCR with confidence scoring and validation rules that route only genuine edge cases to humans.",
    metric: { value: 99.4, decimals: 1, suffix: "%", label: "Field-level accuracy" },
  },
  {
    icon: Building2,
    title: "Enterprise Ready",
    description:
      "SSO via SAML and OIDC, SCIM provisioning, granular RBAC, and contractual uptime backed by SLAs.",
    metric: { value: 99.99, decimals: 2, suffix: "%", label: "Contractual uptime" },
  },
  {
    icon: Network,
    title: "Multi-Organization",
    description:
      "Isolated tenants with independent quotas, routing policies, retention rules, and billing attribution.",
    metric: { value: 500, suffix: "+", label: "Tenants supported" },
  },
  {
    icon: ScrollText,
    title: "Audit Logging",
    description:
      "Immutable, exportable audit trails covering every access, edit, approval, and administrative action.",
    metric: { value: 7, suffix: " yrs", label: "Retention window" },
  },
];

export function TrustSection() {
  return (
    <Section id="trust">
      <SectionHeading
        eyebrow="Built for the enterprise"
        title={
          <>
            Trusted infrastructure for{" "}
            <span className="ai-gradient-text">regulated industries</span>
          </>
        }
        description="Krama AI runs the document backbone for financial services, legal, healthcare, and public sector teams that cannot compromise on security or accuracy."
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
