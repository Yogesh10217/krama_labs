"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
  FileText, 
  Users, 
  Activity, 
  FileCheck, 
  ArrowUpRight, 
  UploadCloud, 
  Server, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar } from "recharts";
import Link from "next/link";
import type { Variants } from "framer-motion";
import { cn } from "@/lib/utils";

const analyticsData = [
  { name: "Mon", docs: 400, errors: 24 },
  { name: "Tue", docs: 300, errors: 13 },
  { name: "Wed", docs: 550, errors: 48 },
  { name: "Thu", docs: 478, errors: 39 },
  { name: "Fri", docs: 589, errors: 28 },
  { name: "Sat", docs: 239, errors: 18 },
  { name: "Sun", docs: 349, errors: 23 },
];

const providerStatus = [
  { name: "OpenAI (GPT-4o)", status: "operational", latency: "120ms" },
  { name: "Anthropic (Claude 3.5)", status: "operational", latency: "145ms" },
  { name: "Internal GPU Cluster", status: "degraded", latency: "850ms" },
];

const recentDocs = [
  { id: "1", file: "Commercial_Invoice_INV-8922.pdf", status: "extracted", time: "2 mins ago" },
  { id: "2", file: "Master_Service_Agreement_MSA-8920.pdf", status: "processing", time: "15 mins ago" },
  { id: "3", file: "Health_Insurance_Claim_CLM-8919.pdf", status: "failed", time: "1 hour ago" },
  { id: "4", file: "Purchase_Order_PO-789.pdf", status: "extracted", time: "3 hours ago" },
];

const queue = [
  { id: "job_991", type: "Batch Extraction", progress: 75, docs: 124 },
  { id: "job_992", type: "Entity Linking", progress: 30, docs: 45 },
];

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export default function DashboardPage() {
  return (
    <div className="p-6 md:p-8 space-y-8 max-w-[1600px] mx-auto pb-20">
      
      {/* Premium Hero */}
      <motion.section
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative overflow-hidden rounded-3xl glass-strong gradient-border p-8 md:p-12"
      >
        {/* Hero orb decoration */}
        <div
          className="absolute -top-32 -right-20 w-[480px] h-[480px] rounded-full blur-3xl opacity-60 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, hsl(262 90% 65% / 0.35), hsl(190 95% 60% / 0.15) 50%, transparent 70%)",
          }}
          aria-hidden="true"
        />
        <div
          className="absolute -bottom-40 -left-20 w-[420px] h-[420px] rounded-full blur-3xl opacity-50 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, hsl(320 90% 65% / 0.22), transparent 70%)",
          }}
          aria-hidden="true"
        />
        {/* Subtle grid behind text */}
        <div className="absolute inset-0 grid-pattern opacity-30" aria-hidden="true" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-8">
          <div className="space-y-5 max-w-2xl">
            <div className="inline-flex items-center gap-2 glass px-3.5 py-1.5 rounded-full">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-[hsl(190_95%_60%)] opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[hsl(190_95%_60%)]" />
              </span>
              <span className="text-xs font-medium tracking-wider uppercase text-foreground/80">
                All systems operational · v4.2
              </span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.05]">
              Document Intelligence for{" "}
              <span className="ai-gradient-text">Insurance Professionals.</span>
            </h1>
            <p className="text-lg text-foreground/70 max-w-xl leading-relaxed">
              Welcome back, Admin. Domain-specific AI that turns discharge summaries, repair estimates, and claim forms into validated decisions in minutes.
            </p>
          </div>

          <div className="flex items-center gap-3 md:flex-col md:items-end">
            <Button
              size="lg"
              className="gap-2 relative overflow-hidden group ai-gradient-bg border-0 text-white font-medium shadow-[0_0_24px_hsl(262_90%_65%_/_0.35)]"
              asChild
            >
              <Link href="/upload">
                <UploadCloud className="w-4 h-4" />
                Quick Upload
                <span
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                  aria-hidden="true"
                />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="gap-2 glass border-white/10 hover:border-white/20 hover:bg-white/[0.04] font-medium"
              asChild
            >
              <Link href="/reports">View Reports</Link>
            </Button>
          </div>
        </div>

        {/* Decorative floating icon cluster */}
        <div
          className="absolute right-6 top-6 hidden lg:flex items-center gap-3 opacity-70"
          aria-hidden="true"
        >
          <div className="glass rounded-xl p-2.5 lift">
            <Sparkles className="w-4 h-4 ai-gradient-text" />
          </div>
        </div>
      </motion.section>

      {/* KPI Cards */}
      <motion.div 
        variants={containerVariants} 
        initial="hidden" 
        animate="show" 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {[
          { title: "Processed This Month", value: "142,394", icon: FileText, trend: "+12.5%", good: true },
          { title: "Avg Extraction Accuracy", value: "99.4%", icon: FileCheck, trend: "+0.2%", good: true },
          { title: "Active API Tokens", value: "24", icon: Users, trend: "+2", good: true },
          { title: "Error Rate", value: "0.8%", icon: Activity, trend: "-0.4%", good: true },
        ].map((stat, i) => (
          <motion.div key={i} variants={itemVariants}>
            <Card className="glass lift gradient-border h-full">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="relative p-2.5 rounded-xl">
                    <div
                      className="absolute inset-0 rounded-xl ai-gradient-bg opacity-20 blur-md"
                      aria-hidden="true"
                    />
                    <div className="relative w-9 h-9 rounded-lg glass flex items-center justify-center">
                      <stat.icon className="w-[18px] h-[18px] text-foreground" />
                    </div>
                  </div>
                  <Badge variant={stat.good ? "success" : "destructive"} className="flex items-center gap-1 font-mono text-xs">
                    {stat.trend.startsWith("+") ? <ArrowUpRight className="w-3 h-3" /> : null}
                    {stat.trend}
                  </Badge>
                </div>
                <div>
                  <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-2 font-medium">
                    {stat.title}
                  </h3>
                  <p className="text-[32px] font-semibold tracking-tight leading-none">
                    {stat.value}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2 space-y-6"
        >
          <Card className="glass h-[420px] flex flex-col lift gradient-border">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-lg">Processing Volume</CardTitle>
                <CardDescription>Documents processed vs. errors over the last 7 days.</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/analytics" className="gap-1 text-primary">Full Analytics <ChevronRight className="w-4 h-4" /></Link>
              </Button>
            </CardHeader>
            <CardContent className="flex-1 pb-6">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analyticsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorDocs" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                    itemStyle={{ color: "hsl(var(--foreground))" }}
                  />
                  <Area type="monotone" dataKey="docs" name="Documents" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#colorDocs)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* System Health */}
            <Card className="glass lift">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Server className="w-4 h-4" /> System Health
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">API Gateway</span>
                    <span className="text-green-500 font-medium flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> 99.99%</span>
                  </div>
                  <Progress value={99} className="h-1.5" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Database Clusters</span>
                    <span className="text-green-500 font-medium flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> 99.95%</span>
                  </div>
                  <Progress value={95} className="h-1.5" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">GPU Workers (Inference)</span>
                    <span className="text-amber-500 font-medium flex items-center gap-1"><AlertCircle className="w-3 h-3" /> 82.00%</span>
                  </div>
                  <Progress value={82} className="h-1.5 [&>div]:bg-amber-500" />
                </div>
              </CardContent>
            </Card>

            {/* Provider Status */}
            <Card className="glass lift">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Provider Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {providerStatus.map((provider, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        provider.status === "operational" ? "bg-green-500" : "bg-amber-500 animate-pulse"
                      )} />
                      <span className="text-sm font-medium">{provider.name}</span>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">{provider.latency}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </motion.div>

        {/* Sidebar Column */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          {/* Active Queue */}
          <Card className="glass lift gradient-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="w-4 h-4 text-primary" /> Processing Queue
                </CardTitle>
                <Badge variant="secondary">{queue.length} Active</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              {queue.map((job, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium truncate pr-4">{job.type}</span>
                    <span className="text-muted-foreground shrink-0">{job.progress}%</span>
                  </div>
                  <Progress value={job.progress} className="h-2" />
                  <p className="text-xs text-muted-foreground text-right">{job.docs} docs remaining</p>
                </div>
              ))}
            </CardContent>
            <CardFooter className="pt-0 pb-4">
              <Button variant="ghost" className="w-full text-xs h-8" asChild>
                <Link href="/jobs">View All Jobs</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Recent Documents */}
          <Card className="glass lift">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Recent Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentDocs.map((doc, i) => (
                <div key={i} className="flex items-start justify-between gap-3 group cursor-pointer">
                  <div className="flex items-start gap-3 overflow-hidden">
                    <div className="mt-0.5 w-8 h-8 rounded bg-secondary flex items-center justify-center shrink-0 group-hover:bg-primary/10 transition-colors">
                      <FileText className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <div className="overflow-hidden">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">{doc.file}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{doc.time}</p>
                    </div>
                  </div>
                  <Badge 
                    variant={doc.status === "extracted" ? "success" : doc.status === "failed" ? "destructive" : "warning"} 
                    className="capitalize shrink-0 text-[10px] px-1.5 py-0"
                  >
                    {doc.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
            <CardFooter className="border-t bg-muted/20 px-4 py-3">
              <Button variant="link" className="w-full text-sm h-8" asChild>
                <Link href="/documents">View Document Library <ChevronRight className="w-4 h-4 ml-1" /></Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Mini Quick Upload */}
          <Card className="glass lift border-dashed border-foreground/10">
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-background rounded-full flex items-center justify-center mx-auto mb-3 border shadow-sm">
                <UploadCloud className="w-5 h-5 text-muted-foreground" />
              </div>
              <h3 className="font-medium text-sm mb-1">Drag & Drop Files</h3>
              <p className="text-xs text-muted-foreground mb-4">Upload documents directly to the extraction queue.</p>
              <Button variant="outline" size="sm" className="w-full bg-background" asChild>
                <Link href="/upload">Open Uploader</Link>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
