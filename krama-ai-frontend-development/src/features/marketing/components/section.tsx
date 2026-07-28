"use client";

import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import { cn } from "@/lib/utils";

/** Shared easing — matches the app-wide ease-out-expo curve. */
export const EASE = [0.22, 1, 0.36, 1] as const;

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: EASE } },
};

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

/** Section wrapper with consistent vertical rhythm + scroll reveal. */
export function Section({
  id,
  children,
  className,
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      id={id}
      className={cn("relative scroll-mt-24 py-24 md:py-32 px-6", className)}
    >
      <div className="mx-auto w-full max-w-[1200px]">{children}</div>
    </section>
  );
}

/** Eyebrow pill — reuses the glass token from the design system. */
export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <motion.div variants={fadeUp} className="flex justify-center">
      <div className="inline-flex items-center gap-2 glass rounded-full px-3.5 py-1.5">
        <span className="h-1.5 w-1.5 rounded-full ai-gradient-bg" aria-hidden="true" />
        <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-foreground/70">
          {children}
        </span>
      </div>
    </motion.div>
  );
}

interface SectionHeadingProps {
  eyebrow?: string;
  title: React.ReactNode;
  description?: string;
  align?: "center" | "left";
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "center",
}: SectionHeadingProps) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-100px" }}
      className={cn(
        "flex flex-col gap-5",
        align === "center" ? "items-center text-center" : "items-start text-left"
      )}
    >
      {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
      <motion.h2
        variants={fadeUp}
        className="max-w-3xl text-balance text-3xl font-semibold leading-[1.12] tracking-tight md:text-[42px]"
      >
        {title}
      </motion.h2>
      {description && (
        <motion.p
          variants={fadeUp}
          className="max-w-2xl text-pretty text-base leading-relaxed text-foreground/60 md:text-lg"
        >
          {description}
        </motion.p>
      )}
    </motion.div>
  );
}
