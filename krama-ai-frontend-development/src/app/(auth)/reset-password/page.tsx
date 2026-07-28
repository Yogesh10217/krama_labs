"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Check, Eye, EyeOff, KeyRound, Loader2, ShieldCheck } from "lucide-react";
import { AuthStatusCard } from "@/features/auth/components/auth-status-card";
import { cn } from "@/lib/utils";

const EASE = [0.22, 1, 0.36, 1] as const;

const resetSchema = z
  .object({
    password: z
      .string()
      .min(1, "Password is required")
      .min(10, "Use at least 10 characters")
      .regex(/[A-Z]/, "Include an uppercase letter")
      .regex(/[0-9]/, "Include a number"),
    confirm: z.string().min(1, "Confirm your password"),
  })
  .refine((data) => data.password === data.confirm, {
    path: ["confirm"],
    message: "Passwords do not match",
  });

type ResetValues = z.infer<typeof resetSchema>;

const RULES = [
  { id: "length", label: "At least 10 characters", test: (v: string) => v.length >= 10 },
  { id: "upper", label: "One uppercase letter", test: (v: string) => /[A-Z]/.test(v) },
  { id: "number", label: "One number", test: (v: string) => /[0-9]/.test(v) },
  { id: "symbol", label: "One symbol (recommended)", test: (v: string) => /[^A-Za-z0-9]/.test(v) },
];

export default function ResetPasswordPage() {
  const [done, setDone] = useState(false);
  const [show, setShow] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResetValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { password: "", confirm: "" },
  });

  const password = watch("password");
  const satisfied = useMemo(() => RULES.filter((r) => r.test(password ?? "")).length, [password]);
  const strength = (satisfied / RULES.length) * 100;

  const onSubmit = async () => {
    // Placeholder for FastAPI POST /auth/reset-password
    await new Promise((resolve) => setTimeout(resolve, 900));
    setDone(true);
  };

  if (done) {
    return (
      <AuthStatusCard
        icon={ShieldCheck}
        tone="success"
        title="Password updated"
        description="Your password has been changed. All other active sessions have been signed out for your security."
        actions={[{ label: "Continue to Sign In", href: "/login" }]}
      />
    );
  }

  return (
    <Card className="glass-strong gradient-border shadow-2xl">
      <CardHeader className="space-y-1 pb-6">
        <CardTitle className="text-center text-2xl font-semibold">Set a new password</CardTitle>
        <CardDescription className="text-center">
          Choose a strong password you haven&apos;t used before on Krama AI.
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <CardContent className="space-y-4">
          {/* New password */}
          <div className="space-y-2">
            <Label htmlFor="password">New password</Label>
            <div className="relative">
              <KeyRound
                className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground/35"
                aria-hidden="true"
              />
              <Input
                id="password"
                type={show ? "text" : "password"}
                autoComplete="new-password"
                placeholder="••••••••••"
                aria-invalid={Boolean(errors.password)}
                aria-describedby="password-rules"
                className="bg-background/40 pl-9 pr-10"
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShow((v) => !v)}
                aria-label={show ? "Hide password" : "Show password"}
                aria-pressed={show}
                className="absolute right-2.5 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-md text-foreground/40 transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {show ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              </button>
            </div>

            {/* Strength meter */}
            <div className="space-y-2 pt-1" id="password-rules">
              <div className="h-1 overflow-hidden rounded-full bg-foreground/[0.08]">
                <motion.div
                  className={cn(
                    "h-full rounded-full",
                    strength <= 25 && "bg-red-500",
                    strength > 25 && strength <= 50 && "bg-amber-500",
                    strength > 50 && strength < 100 && "bg-sky-500",
                    strength === 100 && "ai-gradient-bg"
                  )}
                  animate={{ width: `${strength}%` }}
                  transition={{ duration: 0.4, ease: EASE }}
                />
              </div>
              <ul className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                {RULES.map((rule) => {
                  const ok = rule.test(password ?? "");
                  return (
                    <li key={rule.id} className="flex items-center gap-1.5">
                      <span
                        className={cn(
                          "flex h-3 w-3 shrink-0 items-center justify-center rounded-full transition-colors",
                          ok ? "bg-emerald-500/20" : "bg-foreground/[0.07]"
                        )}
                      >
                        {ok && (
                          <Check className="h-2 w-2 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                        )}
                      </span>
                      <span
                        className={cn(
                          "text-[11px] transition-colors",
                          ok ? "text-foreground/65" : "text-foreground/35"
                        )}
                      >
                        {rule.label}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>

          {/* Confirm */}
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm password</Label>
            <Input
              id="confirm"
              type={show ? "text" : "password"}
              autoComplete="new-password"
              placeholder="••••••••••"
              aria-invalid={Boolean(errors.confirm)}
              aria-describedby={errors.confirm ? "confirm-error" : undefined}
              className="bg-background/40"
              {...register("confirm")}
            />
            <AnimatePresence>
              {errors.confirm && (
                <motion.p
                  id="confirm-error"
                  role="alert"
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-xs text-destructive"
                >
                  {errors.confirm.message}
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col gap-4 pt-2">
          <Button
            type="submit"
            disabled={isSubmitting}
            className="h-11 w-full border-0 ai-gradient-bg font-medium text-white shadow-[0_0_24px_hsl(262_90%_65%_/_0.3)] transition-shadow hover:shadow-[0_0_32px_hsl(262_90%_65%_/_0.45)]"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Updating…
              </span>
            ) : (
              "Update Password"
            )}
          </Button>
          <Link
            href="/login"
            className="flex items-center justify-center gap-2 text-sm text-foreground/50 transition-colors hover:text-primary"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back to Login
          </Link>
        </CardFooter>
      </form>
    </Card>
  );
}
