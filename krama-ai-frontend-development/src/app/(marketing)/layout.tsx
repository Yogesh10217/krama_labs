import type { Metadata } from "next";
import { MotionConfig } from "framer-motion";
import { AmbientBackground } from "@/components/layout/AmbientBackground";
import { LandingNav } from "@/features/marketing/sections/landing-nav";
import { LandingFooter } from "@/features/marketing/sections/footer";

export const metadata: Metadata = {
  title: "Krama AI — Transform Enterprise Documents into Actionable Intelligence",
  description:
    "Upload, analyze, classify, extract, validate, and automate enterprise document workflows using AI-powered OCR and intelligent processing.",
};

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <MotionConfig reducedMotion="user">
      <div className="relative min-h-screen overflow-x-clip">
        {/* Reuses the exact ambient system from the app shell */}
        <AmbientBackground />

        <a
          href="#landing-main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
        >
          Skip to main content
        </a>

        <LandingNav />

        <main id="landing-main" className="relative z-10" tabIndex={-1}>
          {children}
        </main>

        <div className="relative z-10">
          <LandingFooter />
        </div>
      </div>
    </MotionConfig>
  );
}
