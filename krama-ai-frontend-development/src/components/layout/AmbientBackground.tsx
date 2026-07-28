"use client";

import { useEffect, useState } from "react";

/**
 * AmbientBackground — premium canvas rendered behind the app shell.
 *
 * Layers (from back to front):
 *   1. Subtle grid pattern (Linear-style) — fades at edges
 *   2. Aurora blobs (slowly drifting, heavily blurred colored orbs)
 *   3. Noise grain (SVG filter texture, 3.5% opacity, overlay blend)
 *
 * Animations are CSS-driven, long-cycle (26-36s), and honor
 * `prefers-reduced-motion` via media-query disabling.
 */
export function AmbientBackground() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      {/* 1. Grid pattern */}
      <div className="absolute inset-0 grid-pattern opacity-60" />

      {/* 2. Aurora blobs — only mount after hydration to avoid SSR mismatch
            with any client-side randomization (we use static offsets). */}
      <div
        className={[
          "absolute inset-0 transition-opacity duration-[2000ms]",
          mounted ? "opacity-100" : "opacity-0",
        ].join(" ")}
      >
        {/* Primary violet orb */}
        <div
          className="aurora-blob"
          style={{
            width: "620px",
            height: "620px",
            top: "-140px",
            left: "-100px",
            background:
              "radial-gradient(circle, rgba(124, 58, 237, 0.12), transparent 70%)",
          }}
        />
        {/* Secondary cyan orb */}
        <div
          className="aurora-blob delay-1"
          style={{
            width: "520px",
            height: "520px",
            top: "25%",
            right: "-140px",
            background:
              "radial-gradient(circle, rgba(6, 182, 212, 0.1), transparent 70%)",
          }}
        />
        {/* Tertiary pink orb */}
        <div
          className="aurora-blob delay-2"
          style={{
            width: "460px",
            height: "460px",
            bottom: "-100px",
            left: "25%",
            background:
              "radial-gradient(circle, rgba(236, 72, 153, 0.08), transparent 70%)",
          }}
        />
        {/* Indigo accent */}
        <div
          className="aurora-blob delay-3"
          style={{
            width: "400px",
            height: "400px",
            top: "45%",
            left: "8%",
            background:
              "radial-gradient(circle, rgba(99, 102, 241, 0.07), transparent 70%)",
          }}
        />
      </div>

      {/* 3. Noise overlay — provides subtle tactile grain */}
      <div className="absolute inset-0 noise" />

      {/* Vignette — soft outer radial focus */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 60%, rgba(248, 250, 252, 0.7) 100%)",
        }}
      />
    </div>
  );
}
