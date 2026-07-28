"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Menu, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { EASE } from "../components/section";

const NAV_LINKS = [
  { label: "How It Works", href: "#how-it-works" },
  { label: "Claim Types", href: "#claim-types" },
  { label: "Features", href: "#features" },
  { label: "Why Krama", href: "#why" },
  { label: "Contact", href: "#contact" },
];

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, ease: EASE }}
      className="fixed inset-x-0 top-0 z-50 px-4 pt-3 md:pt-4"
    >
      <nav
        aria-label="Main"
        className={cn(
          "mx-auto flex h-14 w-full max-w-[1200px] items-center justify-between rounded-2xl px-3 pl-4 transition-all duration-500",
          scrolled ? "glass-strong gradient-border" : "border border-transparent"
        )}
      >
        {/* Brand */}
        <Link href="/" className="flex shrink-0 items-center gap-2.5">
          <div className="relative">
            <div
              className="absolute inset-0 rounded-lg ai-gradient-bg opacity-60 blur-md"
              aria-hidden="true"
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

        {/* Desktop links */}
        <div className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-lg px-3 py-1.5 text-[13px] font-medium text-foreground/60 transition-colors hover:bg-foreground/[0.05] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Desktop actions */}
        <div className="hidden items-center gap-2 md:flex">
          <Button variant="ghost" size="sm" className="text-[13px] text-foreground/70" asChild>
            <Link href="/login">Request Demo</Link>
          </Button>
          <Button
            size="sm"
            className="group gap-1.5 border-0 ai-gradient-bg text-[13px] font-medium text-white shadow-[0_0_20px_hsl(262_90%_65%_/_0.3)]"
            asChild
          >
            <Link href="/dashboard">
              Get Early Access
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </Button>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-foreground/70 transition-colors hover:bg-foreground/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:hidden"
        >
          {open ? <X className="h-4.5 w-4.5" /> : <Menu className="h-4.5 w-4.5" />}
        </button>
      </nav>

      {/* Mobile sheet */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: EASE }}
            className="glass-strong gradient-border mx-auto mt-2 w-full max-w-[1200px] overflow-hidden rounded-2xl p-3 md:hidden"
          >
            <div className="flex flex-col gap-0.5">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-foreground/70 transition-colors hover:bg-foreground/[0.05] hover:text-foreground"
                >
                  {link.label}
                </a>
              ))}
            </div>
            <div className="mt-3 flex flex-col gap-2 border-t border-foreground/[0.07] pt-3">
              <Button variant="outline" className="glass w-full border-foreground/10" asChild>
                <Link href="/login">Request Demo</Link>
              </Button>
              <Button className="w-full border-0 ai-gradient-bg text-white" asChild>
                <Link href="/dashboard">Get Early Access</Link>
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
