"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Loader2, MailCheck } from "lucide-react";
import { forgotPasswordSchema, type ForgotPasswordValues } from "@/features/auth/schemas";

export default function ForgotPasswordPage() {
  const [sentTo, setSentTo] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = async (values: ForgotPasswordValues) => {
    // Placeholder for FastAPI POST /auth/forgot-password.
    await new Promise((resolve) => setTimeout(resolve, 900));
    setSentTo(values.email);
  };

  return (
    <Card className="border-muted/40 shadow-2xl backdrop-blur-xl bg-card/80 overflow-hidden">
      <AnimatePresence mode="wait">
        {sentTo ? (
          <motion.div
            key="success"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="text-center"
          >
            <CardHeader className="space-y-4 pb-4 pt-8">
              <motion.div
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 18, delay: 0.1 }}
                className="mx-auto w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center border-4 border-background shadow-inner"
              >
                <MailCheck className="w-8 h-8 text-green-600 dark:text-green-400" aria-hidden="true" />
              </motion.div>
              <div>
                <CardTitle className="text-2xl font-semibold">Check your inbox</CardTitle>
                <CardDescription className="mt-2 text-base">
                  We sent a reset link to <strong className="text-foreground">{sentTo}</strong>.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                The link expires in 30 minutes. Didn&apos;t receive it? Check spam or try again.
              </p>
            </CardContent>
            <CardFooter className="flex flex-col gap-3 pb-8">
              <Button variant="outline" className="w-full h-11" onClick={() => setSentTo(null)}>
                Resend Email
              </Button>
              <Link
                href="/login"
                className="flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Back to Login
              </Link>
            </CardFooter>
          </motion.div>
        ) : (
          <motion.div
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -12 }}
          >
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl font-semibold text-center">Reset Password</CardTitle>
              <CardDescription className="text-center">
                Enter your work email address and we&apos;ll send you a link to reset your password.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Work Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@company.com"
                    autoComplete="email"
                    aria-invalid={Boolean(errors.email)}
                    aria-describedby={errors.email ? "email-error" : undefined}
                    className="bg-background/50"
                    {...register("email")}
                  />
                  {errors.email && (
                    <p id="email-error" role="alert" className="text-xs text-destructive">
                      {errors.email.message}
                    </p>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-4 pt-2">
                <Button type="submit" className="w-full h-11" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Sending…
                    </span>
                  ) : (
                    "Send Reset Link"
                  )}
                </Button>
                <Link
                  href="/login"
                  className="flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Back to Login
                </Link>
              </CardFooter>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
