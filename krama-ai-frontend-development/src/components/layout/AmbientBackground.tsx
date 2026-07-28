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
            width: "560px",
            height: "560px",
            top: "-120px",
            left: "-80px",
            background:
              "radial-gradient(circle, hsl(262 90% 65% / 0.55), transparent 70%)",
          }}
        />
        {/* Secondary cyan orb */}
        <div
          className="aurora-blob delay-1"
          style={{
            width: "480px",
            height: "480px",
            top: "30%",
            right: "-120px",
            background:
              "radial-gradient(circle, hsl(190 95% 60% / 0.45), transparent 70%)",
          }}
        />
        {/* Tertiary pink orb */}
        <div
          className="aurora-blob delay-2"
          style={{
            width: "420px",
            height: "420px",
            bottom: "-80px",
            left: "30%",
            background:
              "radial-gradient(circle, hsl(320 90% 65% / 0.35), transparent 70%)",
          }}
        />
        {/* Indigo accent */}
        <div
          className="aurora-blob delay-3"
          style={{
            width: "360px",
            height: "360px",
            top: "50%",
            left: "10%",
            background:
              "radial-gradient(circle, hsl(240 90% 65% / 0.3), transparent 70%)",
          }}
        />
      </div>

      {/* 3. Noise overlay — provides subtle tactile grain */}
      <div className="absolute inset-0 noise" />

      {/* Vignette — darkens edges for depth */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 55%, hsl(240 25% 4% / 0.5) 100%)",
        }}
      />
    </div>
  );
}
