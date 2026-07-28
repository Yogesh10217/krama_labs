"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { BrainCircuit, Globe, Mail } from "lucide-react";
import { EASE } from "../components/section";

/* Brand marks as inline SVG (lucide no longer ships brand icons). */
type IconProps = { className?: string };

const GithubIcon = ({ className }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path d="M12 .5a12 12 0 0 0-3.79 23.4c.6.1.82-.26.82-.58v-2.2c-3.34.72-4.04-1.42-4.04-1.42-.55-1.4-1.34-1.77-1.34-1.77-1.1-.75.08-.73.08-.73 1.21.09 1.85 1.25 1.85 1.25 1.08 1.84 2.83 1.31 3.52 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.34-5.47-5.96 0-1.32.47-2.39 1.24-3.23-.13-.3-.54-1.53.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6.01 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.65.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.23 0 4.63-2.81 5.65-5.49 5.95.43.37.82 1.1.82 2.22v3.29c0 .32.21.69.82.58A12 12 0 0 0 12 .5Z" />
  </svg>
);

const LinkedinIcon = ({ className }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05a3.74 3.74 0 0 1 3.37-1.85c3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13Zm1.78 13.02H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0Z" />
  </svg>
);

const XIcon = ({ className }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path d="M18.24 2.25h3.31l-7.23 8.26 8.5 11.24h-6.65l-5.22-6.82-5.96 6.82H1.68l7.73-8.84L1.25 2.25h6.82l4.71 6.23 5.46-6.23Zm-1.16 17.52h1.83L7.02 4.13H5.05l12.03 15.64Z" />
  </svg>
);

const COLUMNS = [
  {
    heading: "Product",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Upload", href: "/upload" },
      { label: "Human Review", href: "/review" },
      { label: "Analytics", href: "/analytics" },
      { label: "Models", href: "/models" },
    ],
  },
  {
    heading: "Company",
    links: [
      { label: "About", href: "#" },
      { label: "Careers", href: "#" },
      { label: "Customers", href: "#" },
      { label: "Newsroom", href: "#" },
      { label: "Security", href: "#trust" },
    ],
  },
  {
    heading: "Resources",
    links: [
      { label: "Documentation", href: "#" },
      { label: "API Reference", href: "#" },
      { label: "Changelog", href: "#" },
      { label: "System Status", href: "/health" },
      { label: "Support", href: "#" },
    ],
  },
  {
    heading: "Legal",
    links: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
      { label: "Data Processing", href: "#" },
      { label: "Sub-processors", href: "#" },
      { label: "Contact", href: "#" },
    ],
  },
];

const SOCIALS = [
  { label: "GitHub", href: "#", icon: GithubIcon },
  { label: "LinkedIn", href: "#", icon: LinkedinIcon },
  { label: "X (Twitter)", href: "#", icon: XIcon },
  { label: "Email", href: "#", icon: Mail },
];

export function LandingFooter() {
  return (
    <footer className="relative border-t border-foreground/[0.07] px-6 pb-10 pt-20">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, hsl(262 90% 65% / 0.4), transparent)",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.7, ease: EASE }}
        className="mx-auto w-full max-w-[1200px]"
      >
        <div className="grid grid-cols-2 gap-10 md:grid-cols-3 lg:grid-cols-6">
          {/* Brand block */}
          <div className="col-span-2 lg:col-span-2">
            <Link href="/" className="inline-flex items-center gap-2.5">
              <div className="relative">
                <div
                  aria-hidden="true"
                  className="absolute inset-0 rounded-lg ai-gradient-bg opacity-55 blur-md"
                />
                <div className="relative rounded-lg bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)] p-1.5 text-white shadow-lg">
                  <BrainCircuit className="h-4 w-4" />
                </div>
              </div>
              <span className="text-[15px] font-semibold tracking-tight">
                <span className="ai-gradient-text">Krama</span>{" "}
                <span className="text-foreground/90">AI</span>
              </span>
            </Link>

            <p className="mt-4 max-w-xs text-[13px] leading-relaxed text-foreground/45">
              Enterprise AI Document Intelligence. Turn unstructured documents into
              validated, auditable data at any scale.
            </p>

            <div className="mt-5 flex items-center gap-2">
              {SOCIALS.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  aria-label={social.label}
                  className="glass flex h-8 w-8 items-center justify-center rounded-lg text-foreground/45 transition-all duration-300 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <social.icon className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
              ))}
            </div>

            <div className="mt-5 inline-flex items-center gap-2 glass rounded-full px-3 py-1.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
              </span>
              <span className="text-[11px] text-foreground/55">All systems operational</span>
            </div>
          </div>

          {/* Link columns */}
          {COLUMNS.map((column) => (
            <nav key={column.heading} aria-label={column.heading}>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-foreground/40">
                {column.heading}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="group inline-flex text-[13px] text-foreground/55 transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span className="relative">
                        {link.label}
                        <span
                          aria-hidden="true"
                          className="absolute -bottom-0.5 left-0 h-px w-0 ai-gradient-bg transition-all duration-300 group-hover:w-full"
                        />
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-foreground/[0.07] pt-7 sm:flex-row">
          <p className="text-xs text-foreground/35">
            © {new Date().getFullYear()} Krama AI, Inc. All rights reserved.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
            {["SOC 2 Type II", "ISO 27001", "GDPR", "HIPAA"].map((badge) => (
              <span
                key={badge}
                className="text-[11px] font-medium uppercase tracking-wider text-foreground/30"
              >
                {badge}
              </span>
            ))}
            <span className="flex items-center gap-1.5 text-xs text-foreground/35">
              <Globe className="h-3 w-3" aria-hidden="true" /> English
            </span>
          </div>
        </div>
      </motion.div>
    </footer>
  );
}
