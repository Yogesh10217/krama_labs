"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { MailCheck, Loader2, ShieldCheck, RefreshCw } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AuthStatusCard } from "@/features/auth/components/auth-status-card";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;
const CODE_LENGTH = 6;
const RESEND_SECONDS = 45;

export default function VerifyEmailPage() {
  const router = useRouter();
  const [digits, setDigits] = useState<string[]>(Array(CODE_LENGTH).fill(""));
  const [status, setStatus] = useState<"idle" | "verifying" | "verified" | "error">("idle");
  const [cooldown, setCooldown] = useState(RESEND_SECONDS);
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);

  // Resend cooldown timer.
  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  const submitCode = async (code: string) => {
    setStatus("verifying");
    await new Promise((resolve) => setTimeout(resolve, 1100));
    // Placeholder: "000000" simulates an invalid code.
    if (code === "000000") {
      setStatus("error");
      setDigits(Array(CODE_LENGTH).fill(""));
      inputsRef.current[0]?.focus();
      return;
    }
    setStatus("verified");
    setTimeout(() => router.push("/dashboard"), 1600);
  };

  const setDigitAt = (index: number, value: string) => {
    const next = [...digits];
    next[index] = value;
    setDigits(next);
    if (status === "error") setStatus("idle");
    const code = next.join("");
    if (code.length === CODE_LENGTH && next.every(Boolean)) void submitCode(code);
  };

  const onChange = (index: number, raw: string) => {
    const value = raw.replace(/\D/g, "");
    if (!value) {
      setDigitAt(index, "");
      return;
    }
    if (value.length > 1) {
      // Paste support
      const chars = value.slice(0, CODE_LENGTH - index).split("");
      const next = [...digits];
      chars.forEach((c, i) => (next[index + i] = c));
      setDigits(next);
      const target = Math.min(index + chars.length, CODE_LENGTH - 1);
      inputsRef.current[target]?.focus();
      const code = next.join("");
      if (code.length === CODE_LENGTH && next.every(Boolean)) void submitCode(code);
      return;
    }
    setDigitAt(index, value);
    if (index < CODE_LENGTH - 1) inputsRef.current[index + 1]?.focus();
  };

  const onKeyDown = (index: number, event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
    if (event.key === "ArrowLeft" && index > 0) inputsRef.current[index - 1]?.focus();
    if (event.key === "ArrowRight" && index < CODE_LENGTH - 1) inputsRef.current[index + 1]?.focus();
  };

  if (status === "verified") {
    return (
      <AuthStatusCard
        icon={ShieldCheck}
        tone="success"
        title="Email verified"
        description="Your address is confirmed. Redirecting you to your workspace…"
        body={
          <div className="flex items-center justify-center gap-2 text-sm text-foreground/50">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            Preparing your dashboard
          </div>
        }
      />
    );
  }

  return (
    <Card className="glass-strong gradient-border text-center shadow-2xl">
      <CardHeader className="space-y-4 pb-4 pt-9">
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 280, damping: 18, delay: 0.1 }}
          className="relative mx-auto"
        >
          <span
            aria-hidden="true"
            className="absolute inset-0 rounded-full ai-gradient-bg opacity-30 blur-lg"
          />
          <span className="relative flex h-16 w-16 items-center justify-center rounded-full border-4 border-background bg-foreground/[0.06] shadow-inner">
            <MailCheck className="h-7 w-7 text-primary" aria-hidden="true" />
          </span>
        </motion.div>
        <div>
          <CardTitle className="text-2xl font-semibold tracking-tight">
            Verify your email
          </CardTitle>
          <CardDescription className="mx-auto mt-2 max-w-sm text-[15px] leading-relaxed">
            We sent a 6-digit code to{" "}
            <strong className="text-foreground">admin@krama.ai</strong>. Enter it below to
            activate your account.
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* OTP inputs */}
        <div
          className="flex justify-center gap-2"
          role="group"
          aria-label="Six digit verification code"
        >
          {digits.map((digit, i) => (
            <input
              key={i}
              ref={(el) => {
                inputsRef.current[i] = el;
              }}
              value={digit}
              onChange={(e) => onChange(i, e.target.value)}
              onKeyDown={(e) => onKeyDown(i, e)}
              disabled={status === "verifying"}
              inputMode="numeric"
              autoComplete={i === 0 ? "one-time-code" : "off"}
              maxLength={CODE_LENGTH}
              aria-label={`Digit ${i + 1}`}
              aria-invalid={status === "error"}
              className={cn(
                "glass h-13 w-11 rounded-xl text-center text-lg font-semibold tabular-nums transition-all sm:h-14 sm:w-12",
                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background",
                "disabled:opacity-60",
                status === "error" && "ring-1 ring-destructive",
                digit && "border-primary/40"
              )}
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          {status === "verifying" && (
            <motion.p
              key="verifying"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: EASE }}
              className="flex items-center justify-center gap-2 text-sm text-foreground/55"
            >
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> Verifying code…
            </motion.p>
          )}
          {status === "error" && (
            <motion.p
              key="error"
              role="alert"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: EASE }}
              className="text-sm text-destructive"
            >
              That code isn&apos;t valid or has expired. Please try again.
            </motion.p>
          )}
        </AnimatePresence>
      </CardContent>

      <CardFooter className="flex flex-col gap-3 pb-8 pt-4">
        <Button
          variant="outline"
          disabled={cooldown > 0}
          onClick={() => setCooldown(RESEND_SECONDS)}
          className="glass h-11 w-full gap-2 border-foreground/10 font-medium hover:border-foreground/20 hover:bg-foreground/[0.05]"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend verification code"}
        </Button>
        <p className="text-xs text-foreground/40">
          Wrong address?{" "}
          <Link href="/login" className="font-medium text-primary hover:text-primary/80">
            Sign in with a different account
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
