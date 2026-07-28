import Link from "next/link";
import { FileQuestion, ArrowLeft, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-6">
      {/* Ambient wash — matches the auth + marketing background language */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute -left-[10%] -top-[20%] h-[60%] w-[60%] rounded-full opacity-55 blur-[120px]"
          style={{ background: "radial-gradient(circle, hsl(262 90% 65% / 0.4), transparent 70%)" }}
        />
        <div
          className="absolute -right-[10%] top-[55%] h-[50%] w-[50%] rounded-full opacity-45 blur-[120px]"
          style={{ background: "radial-gradient(circle, hsl(190 95% 60% / 0.3), transparent 70%)" }}
        />
        <div className="absolute inset-0 grid-pattern opacity-40" />
        <div className="absolute inset-0 noise" />
      </div>

      <div className="glass-strong gradient-border relative z-10 w-full max-w-md rounded-2xl px-8 py-12 text-center shadow-2xl">
        <div className="relative mx-auto mb-6 w-fit">
          <span
            aria-hidden="true"
            className="absolute inset-0 rounded-full ai-gradient-bg opacity-25 blur-lg"
          />
          <span className="relative flex h-16 w-16 items-center justify-center rounded-full border-4 border-background bg-foreground/[0.06] shadow-inner">
            <FileQuestion className="h-7 w-7 text-foreground/55" aria-hidden="true" />
          </span>
        </div>

        <p className="mb-1.5 font-mono text-xs tracking-[0.2em] text-foreground/35">404</p>
        <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="mx-auto mt-2 max-w-sm text-[15px] leading-relaxed text-foreground/55">
          The page you&apos;re looking for doesn&apos;t exist or may have been moved.
        </p>

        <div className="mt-8 flex flex-col gap-2.5 sm:flex-row">
          <Button
            className="h-11 w-full gap-2 border-0 ai-gradient-bg font-medium text-white shadow-[0_0_24px_hsl(262_90%_65%_/_0.3)]"
            asChild
          >
            <Link href="/dashboard">
              <LayoutDashboard className="h-4 w-4" aria-hidden="true" /> Go to Dashboard
            </Link>
          </Button>
          <Button
            variant="outline"
            className="glass h-11 w-full gap-2 border-foreground/10 font-medium hover:border-foreground/20 hover:bg-foreground/[0.05]"
            asChild
          >
            <Link href="/">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Home
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
