"use client";

import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { ArrowRight, Play, ScanText, ShieldCheck, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ParticleField } from "../components/particle-field";
import { AnimatedCounter } from "../components/animated-counter";
import { DashboardMockup } from "../components/mockups";
import { EASE, fadeUp, staggerContainer } from "../components/section";

/** Floating geometric accents — AI-inspired, low opacity, slow drift. */
function FloatingGeometry() {
  const shapes = [
    { Icon: ScanText, top: "16%", left: "4%", delay: 0, size: 46 },
    { Icon: Layers, top: "62%", left: "7%", delay: 1.2, size: 40 },
    { Icon: ShieldCheck, top: "78%", left: "44%", delay: 2.1, size: 38 },
  ];

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 hidden lg:block">
      {shapes.map(({ Icon, top, left, delay, size }, i) => (
        <motion.div
          key={i}
          className="absolute glass flex items-center justify-center rounded-2xl"
          style={{ top, left, width: size, height: size }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{
            opacity: 0.55,
            scale: 1,
            y: [0, -12, 0],
            rotate: [0, 4, 0],
          }}
          transition={{
            opacity: { duration: 1, delay: 0.8 + delay * 0.2 },
            scale: { duration: 1, delay: 0.8 + delay * 0.2, ease: EASE },
            y: { duration: 8 + i * 1.5, repeat: Infinity, ease: "easeInOut", delay },
            rotate: { duration: 10 + i * 2, repeat: Infinity, ease: "easeInOut", delay },
          }}
        >
          <Icon className="h-4 w-4 text-foreground/50" />
        </motion.div>
      ))}

      {/* Wireframe rings */}
      <motion.div
        className="absolute -right-24 top-[12%] h-64 w-64 rounded-full border border-foreground/[0.07]"
        animate={{ rotate: 360 }}
        transition={{ duration: 90, repeat: Infinity, ease: "linear" }}
      >
        <span className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rounded-full bg-[hsl(190_95%_60%)] shadow-[0_0_12px_hsl(190_95%_60%)]" />
      </motion.div>
      <motion.div
        className="absolute -left-32 bottom-[6%] h-80 w-80 rounded-full border border-foreground/[0.05]"
        animate={{ rotate: -360 }}
        transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
      >
        <span className="absolute -bottom-1 left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[hsl(320_90%_65%)] shadow-[0_0_10px_hsl(320_90%_65%)]" />
      </motion.div>
    </div>
  );
}

const HERO_STATS = [
  { value: 8000, suffix: " Cr", label: "Fraud Prevented" },
  { value: 99.4, decimals: 1, suffix: "%", label: "Extraction accuracy" },
  { value: 8, suffix: "x", label: "Faster Processing" },
];

export function Hero() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const mockY = useTransform(scrollYProgress, [0, 1], [0, -60]);
  const copyY = useTransform(scrollYProgress, [0, 1], [0, 40]);
  const fade = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  return (
    <section
      ref={ref}
      className="relative flex min-h-screen items-center overflow-hidden px-6 pb-20 pt-32 md:pt-36"
    >
      <ParticleField count={30} seed={11} />
      <FloatingGeometry />

      <div className="relative z-10 mx-auto grid w-full max-w-[1200px] items-center gap-14 lg:grid-cols-[1.05fr_1fr] lg:gap-12">
        {/* ---------------- Copy ---------------- */}
        <motion.div
          style={{ y: copyY, opacity: fade }}
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="flex flex-col items-start gap-7"
        >
          <motion.div variants={fadeUp}>
            <div className="inline-flex items-center gap-2 glass rounded-full py-1.5 pl-1.5 pr-3.5">
              <span className="rounded-full ai-gradient-bg px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white">
                🚀 Early Access
              </span>
              <span className="text-xs font-medium text-foreground/70">
                Building with India's Top Insurers
              </span>
            </div>
          </motion.div>

          <motion.h1
            variants={fadeUp}
            className="max-w-[15ch] text-balance text-[40px] font-semibold leading-[1.03] tracking-tight sm:text-[54px] lg:text-[62px]"
          >
            Document Intelligence for{" "}
            <span className="ai-gradient-text">Insurance Professionals</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="max-w-xl text-pretty text-base leading-relaxed text-foreground/60 md:text-lg"
          >
            Domain-specific AI that turns discharge summaries, repair estimates, and claim forms into validated, fraud-checked decisions in minutes, not days.
          </motion.p>

          <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-3">
            <Button
              size="lg"
              className="group h-12 gap-2 border-0 ai-gradient-bg px-6 text-[15px] font-medium text-white shadow-[0_0_32px_hsl(262_90%_65%_/_0.35)] transition-shadow hover:shadow-[0_0_44px_hsl(262_90%_65%_/_0.5)]"
              asChild
            >
              <Link href="/dashboard">
                Get Early Access
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="group glass h-12 gap-2.5 border-foreground/10 px-5 text-[15px] font-medium hover:border-foreground/20 hover:bg-foreground/[0.04]"
              asChild
            >
              <Link href="#product">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-foreground/[0.08] transition-colors group-hover:bg-foreground/[0.14]">
                  <Play className="h-2.5 w-2.5 fill-current" />
                </span>
                Learn More
              </Link>
            </Button>
          </motion.div>

          {/* Inline stats */}
          <motion.dl
            variants={fadeUp}
            className="mt-2 grid w-full max-w-lg grid-cols-3 gap-6 border-t border-foreground/[0.07] pt-7"
          >
            {HERO_STATS.map((stat) => (
              <div key={stat.label}>
                <dt className="sr-only">{stat.label}</dt>
                <dd className="text-2xl font-semibold tracking-tight text-foreground/90">
                  <AnimatedCounter
                    value={stat.value}
                    decimals={stat.decimals ?? 0}
                    suffix={stat.suffix}
                  />
                </dd>
                <p className="mt-1 text-[11px] uppercase tracking-wider text-foreground/40">
                  {stat.label}
                </p>
              </div>
            ))}
          </motion.dl>
        </motion.div>

        {/* ---------------- Mockup ---------------- */}
        <motion.div
          style={{ y: mockY }}
          initial={{ opacity: 0, x: 40, rotateY: -8 }}
          animate={{ opacity: 1, x: 0, rotateY: 0 }}
          transition={{ duration: 1, delay: 0.25, ease: EASE }}
          className="relative [perspective:1400px]"
        >
          {/* Glow behind the panel */}
          <div
            aria-hidden="true"
            className="absolute -inset-8 rounded-[32px] opacity-70 blur-3xl"
            style={{
              background:
                "radial-gradient(circle at 60% 40%, hsl(262 90% 65% / 0.3), hsl(190 95% 60% / 0.12) 55%, transparent 75%)",
            }}
          />

          {/* Depth: stacked ghost panels behind */}
          <div
            aria-hidden="true"
            className="absolute -right-5 -top-5 hidden h-full w-full rounded-2xl border border-foreground/[0.06] bg-foreground/[0.02] sm:block"
          />
          <div
            aria-hidden="true"
            className="absolute -right-2.5 -top-2.5 hidden h-full w-full rounded-2xl border border-foreground/[0.08] bg-foreground/[0.03] sm:block"
          />

          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
            className="relative"
          >
            <DashboardMockup />
          </motion.div>

          {/* Floating callout chips */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1, y: [0, -7, 0] }}
            transition={{
              opacity: { duration: 0.6, delay: 1.1 },
              scale: { duration: 0.6, delay: 1.1, ease: EASE },
              y: { duration: 6, repeat: Infinity, ease: "easeInOut", delay: 1.1 },
            }}
            className="glass-strong absolute -left-4 bottom-10 hidden items-center gap-2 rounded-xl px-3 py-2 sm:flex"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-lg ai-gradient-bg">
              <ScanText className="h-3 w-3 text-white" />
            </span>
            <div>
              <p className="text-[11px] font-semibold leading-none">OCR complete</p>
              <p className="mt-0.5 text-[9px] text-foreground/45">2,048 pages · 1.2s</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1, y: [0, 8, 0] }}
            transition={{
              opacity: { duration: 0.6, delay: 1.35 },
              scale: { duration: 0.6, delay: 1.35, ease: EASE },
              y: { duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1.35 },
            }}
            className="glass-strong absolute -right-3 top-14 hidden items-center gap-2 rounded-xl px-3 py-2 lg:flex"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <p className="text-[11px] font-medium text-foreground/80">99.4% confidence</p>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom fade into next section */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 h-32 bg-gradient-to-b from-transparent to-background"
      />
    </section>
  );
}
