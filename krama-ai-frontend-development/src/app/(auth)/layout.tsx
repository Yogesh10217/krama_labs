"use client";

import { motion } from "framer-motion";
import { BrainCircuit } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-background relative overflow-hidden">
      {/* Ambient background orbs */}
      <div
        className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none"
        aria-hidden="true"
      >
        <div className="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full blur-[120px] opacity-60"
          style={{ background: "radial-gradient(circle, hsl(262 90% 65% / 0.45), transparent 70%)" }}
        />
        <div className="absolute top-[60%] -right-[10%] w-[50%] h-[50%] rounded-full blur-[120px] opacity-50"
          style={{ background: "radial-gradient(circle, hsl(190 95% 60% / 0.35), transparent 70%)" }}
        />
        <div className="absolute bottom-[-10%] left-[30%] w-[40%] h-[40%] rounded-full blur-[120px] opacity-40"
          style={{ background: "radial-gradient(circle, hsl(320 90% 65% / 0.28), transparent 70%)" }}
        />
        <div className="absolute inset-0 grid-pattern opacity-40" />
        <div className="absolute inset-0 noise" />
      </div>

      <div className="relative z-10 w-full max-w-md p-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="flex justify-center mb-8"
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              <div
                className="absolute inset-0 rounded-xl ai-gradient-bg opacity-60 blur-lg"
                aria-hidden="true"
              />
              <div className="relative bg-gradient-to-br from-[hsl(190_95%_55%)] via-primary to-[hsl(320_90%_65%)] text-white p-2.5 rounded-xl shadow-xl">
                <BrainCircuit className="w-6 h-6" />
              </div>
            </div>
            <span className="font-bold text-2xl tracking-tight">
              <span className="ai-gradient-text">Krama</span>{" "}
              <span className="text-foreground/90">AI</span>
            </span>
          </div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          {children}
        </motion.div>
      </div>
    </div>
  );
}
