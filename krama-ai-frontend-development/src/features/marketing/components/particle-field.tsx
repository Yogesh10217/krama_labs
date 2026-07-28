"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

/** Deterministic PRNG so server and client render identical particles. */
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const TINTS = [
  "hsl(190 95% 65%)",
  "hsl(262 90% 72%)",
  "hsl(320 90% 72%)",
  "hsl(220 20% 95%)",
];

/**
 * ParticleField — drifting luminous motes.
 * Subtle by design: low opacity, long durations, no interaction cost.
 */
export function ParticleField({
  count = 28,
  seed = 7,
  className = "",
}: {
  count?: number;
  seed?: number;
  className?: string;
}) {
  const particles = useMemo(() => {
    const rand = mulberry32(seed);
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      x: rand() * 100,
      y: rand() * 100,
      size: 1 + rand() * 2.5,
      drift: 30 + rand() * 70,
      duration: 14 + rand() * 16,
      delay: rand() * -20,
      opacity: 0.25 + rand() * 0.45,
      tint: TINTS[Math.floor(rand() * TINTS.length)],
    }));
  }, [count, seed]);

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
    >
      {particles.map((p) => (
        <motion.span
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: p.tint,
            boxShadow: `0 0 ${p.size * 4}px ${p.tint}`,
          }}
          initial={{ opacity: 0 }}
          animate={{
            y: [0, -p.drift, 0],
            x: [0, p.drift * 0.25, 0],
            opacity: [0, p.opacity, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
