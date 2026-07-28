"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CalendarCheck, ShieldCheck, Clock, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ParticleField } from "../components/particle-field";
import { EASE, fadeUp, staggerContainer } from "../components/section";

const ASSURANCES = [
  { icon: Clock, label: "Deploy in under 2 weeks" },
  { icon: CreditCard, label: "No credit card required" },
  { icon: ShieldCheck, label: "SOC 2 Type II certified" },
];

export function CtaSection() {
  return (
    <section className="relative px-6 py-24 md:py-32">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-100px" }}
        className="relative mx-auto w-full max-w-[1100px] overflow-hidden rounded-[28px] glass-strong gradient-border px-6 py-16 text-center md:px-16 md:py-24"
      >
        {/* Aurora wash */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-40 left-1/2 h-[420px] w-[720px] -translate-x-1/2 rounded-full blur-3xl"
          style={{
            background:
              "radial-gradient(circle, hsl(262 90% 65% / 0.32), hsl(190 95% 60% / 0.14) 50%, transparent 72%)",
          }}
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-32 right-0 h-[320px] w-[420px] rounded-full blur-3xl"
          style={{
            background: "radial-gradient(circle, hsl(320 90% 65% / 0.2), transparent 70%)",
          }}
        />
        <div aria-hidden="true" className="absolute inset-0 grid-pattern opacity-30" />
        <ParticleField count={18} seed={23} />

        <div className="relative z-10 flex flex-col items-center gap-7">
          <motion.div variants={fadeUp}>
            <div className="inline-flex items-center gap-2 glass rounded-full px-3.5 py-1.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[hsl(190_95%_60%)] opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[hsl(190_95%_60%)]" />
              </span>
              <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-foreground/70">
                Now onboarding enterprise teams
              </span>
            </div>
          </motion.div>

          <motion.h2
            variants={fadeUp}
            className="max-w-[18ch] text-balance text-[32px] font-semibold leading-[1.08] tracking-tight md:text-[48px]"
          >
            Ready to Modernize Your{" "}
            <span className="ai-gradient-text">Document Processing?</span>
          </motion.h2>

          <motion.p
            variants={fadeUp}
            className="max-w-xl text-pretty text-base leading-relaxed text-foreground/60"
          >
            Join the teams replacing manual keying with an auditable, AI-native
            pipeline. Start in a sandbox today, or talk to our solutions engineers
            about a private deployment.
          </motion.p>

          <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-3">
            <Button
              size="lg"
              className="group h-12 gap-2 border-0 ai-gradient-bg px-7 text-[15px] font-medium text-white shadow-[0_0_32px_hsl(262_90%_65%_/_0.4)] transition-shadow hover:shadow-[0_0_48px_hsl(262_90%_65%_/_0.55)]"
              asChild
            >
              <Link href="/login">
                <CalendarCheck className="h-4 w-4" />
                Request Demo
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="group glass h-12 gap-2 border-foreground/12 px-7 text-[15px] font-medium hover:border-foreground/25 hover:bg-foreground/[0.05]"
              asChild
            >
              <Link href="/dashboard">
                Start Free Trial
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
          </motion.div>

          <motion.ul
            variants={fadeUp}
            className="mt-3 flex flex-wrap items-center justify-center gap-x-7 gap-y-2.5"
          >
            {ASSURANCES.map((item) => (
              <li key={item.label} className="flex items-center gap-2">
                <item.icon className="h-3.5 w-3.5 text-foreground/35" aria-hidden="true" />
                <span className="text-xs text-foreground/45">{item.label}</span>
              </li>
            ))}
          </motion.ul>
        </div>
      </motion.div>
    </section>
  );
}
