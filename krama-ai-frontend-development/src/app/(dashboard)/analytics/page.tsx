"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  BarChart, Bar, PieChart, Pie, Cell, Legend, LineChart, Line
} from "recharts";
import {
  FileText, DollarSign, Gauge, Database, ScanText, Building2, Layers, Target
} from "lucide-react";
import { KpiCard, ExportDialog, RangeFilter, AnalyticsHeader, chartTooltipStyle } from "@/features/analytics/components";

const volumeData = [
  { name: "W1", docs: 8200, pages: 41200, cost: 620 },
  { name: "W2", docs: 9400, pages: 47800, cost: 710 },
  { name: "W3", docs: 7600, pages: 39100, cost: 590 },
  { name: "W4", docs: 11800, pages: 60300, cost: 880 },
  { name: "W5", docs: 12400, pages: 63900, cost: 940 },
  { name: "W6", docs: 10900, pages: 55600, cost: 810 },
  { name: "W7", docs: 14100, pages: 72400, cost: 1050 },
  { name: "W8", docs: 15200, pages: 78100, cost: 1120 },
];

const providerCosts = [
  { name: "OpenAI", value: 4820, color: "#10b981" },
  { name: "Anthropic", value: 3610, color: "#8b5cf6" },
  { name: "Google", value: 1290, color: "#3b82f6" },
  { name: "Internal GPU", value: 2140, color: "#f59e0b" },
];

const ocrAccuracy = [
  { name: "Jan", printed: 99.1, handwritten: 91.2 },
  { name: "Feb", printed: 99.2, handwritten: 92.0 },
  { name: "Mar", printed: 99.4, handwritten: 92.8 },
  { name: "Apr", printed: 99.3, handwritten: 93.5 },
  { name: "May", printed: 99.5, handwritten: 94.1 },
  { name: "Jun", printed: 99.6, handwritten: 94.9 },
];

const extractionByType = [
  { name: "Invoices", success: 96, review: 3, failed: 1 },
  { name: "Contracts", success: 89, review: 9, failed: 2 },
  { name: "Receipts", success: 93, review: 5, failed: 2 },
  { name: "Tax Forms", success: 91, review: 7, failed: 2 },
  { name: "ID Docs", success: 97, review: 2, failed: 1 },
];

const orgUsage = [
  { name: "Acme Corporation", docs: 84200, cost: "$6,410", storage: "1.2 TB", pct: 58 },
  { name: "Globex Inc", docs: 32800, cost: "$2,940", storage: "540 GB", pct: 23 },
  { name: "Soylent Corp", docs: 18100, cost: "$1,610", storage: "310 GB", pct: 12 },
  { name: "Initech LLC", docs: 9400, cost: "$860", storage: "150 GB", pct: 7 },
];

export default function AnalyticsPage() {
  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1600px] mx-auto pb-20">
      <AnalyticsHeader
        title="Analytics"
        description="Executive insights across processing, cost, and quality."
      >
        <RangeFilter />
        <ExportDialog />
      </AnalyticsHeader>

      {/* Top KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard index={0} title="Documents Processed" value="142,394" trend="+12.5%" icon={FileText} subtitle="vs. previous period" />
        <KpiCard index={1} title="Total Spend" value="$11,860" trend="+8.2%" trendPositive={false} icon={DollarSign} subtitle="across all providers" />
        <KpiCard index={2} title="Avg Accuracy" value="99.4%" trend="+0.2%" icon={Target} subtitle="weighted by volume" />
        <KpiCard index={3} title="Storage Used" value="2.2 TB" trend="+140 GB" icon={Database} subtitle="of 5 TB quota" />
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="cost">Cost</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="ocr">OCR Metrics</TabsTrigger>
          <TabsTrigger value="extraction">Extraction</TabsTrigger>
          <TabsTrigger value="orgs">Organizations</TabsTrigger>
          <TabsTrigger value="storage">Storage</TabsTrigger>
        </TabsList>

        {/* ---------- Overview ---------- */}
        <TabsContent value="overview" className="space-y-6">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <CardTitle>Processing Volume</CardTitle>
                <CardDescription>Documents and pages processed over the last 8 weeks.</CardDescription>
              </CardHeader>
              <CardContent className="h-[360px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={volumeData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gDocs" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gPages" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip {...chartTooltipStyle} />
                    <Legend />
                    <Area type="monotone" dataKey="pages" name="Pages" stroke="#10b981" strokeWidth={2} fill="url(#gPages)" />
                    <Area type="monotone" dataKey="docs" name="Documents" stroke="hsl(var(--primary))" strokeWidth={2} fill="url(#gDocs)" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* ---------- Cost ---------- */}
        <TabsContent value="cost" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Weekly Spend</CardTitle>
                <CardDescription>Inference and OCR costs across all providers (USD).</CardDescription>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={volumeData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
                    <Tooltip {...chartTooltipStyle} formatter={(value) => [`$${value}`, "Cost"]} />
                    <Bar dataKey="cost" name="Cost" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Cost by Provider</CardTitle>
                <CardDescription>Current billing period.</CardDescription>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="70%">
                  <PieChart>
                    <Pie data={providerCosts} dataKey="value" nameKey="name" innerRadius={55} outerRadius={80} paddingAngle={4} strokeWidth={0}>
                      {providerCosts.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip {...chartTooltipStyle} formatter={(value) => [`$${value}`, ""]} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1.5">
                  {providerCosts.map((p) => (
                    <div key={p.name} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
                        <span className="text-muted-foreground">{p.name}</span>
                      </div>
                      <span className="font-mono font-medium">${p.value.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ---------- Providers ---------- */}
        <TabsContent value="providers" className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard index={0} title="OpenAI Requests" value="1.2M" trend="+18%" icon={Layers} subtitle="p95 latency 420ms" />
            <KpiCard index={1} title="Anthropic Requests" value="840K" trend="+9%" icon={Layers} subtitle="p95 latency 510ms" />
            <KpiCard index={2} title="Google Requests" value="210K" trend="-4%" trendPositive={false} icon={Layers} subtitle="p95 latency 380ms" />
            <KpiCard index={3} title="Internal GPU" value="460K" trend="+31%" icon={Gauge} subtitle="p95 latency 890ms" />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Provider Latency Trends</CardTitle>
              <CardDescription>p95 response latency by provider (ms).</CardDescription>
            </CardHeader>
            <CardContent className="h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ocrAccuracy.map((d, i) => ({ name: d.name, openai: 400 + i * 8, anthropic: 500 + i * 5, internal: 950 - i * 12 }))} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip {...chartTooltipStyle} />
                  <Legend />
                  <Line type="monotone" dataKey="openai" name="OpenAI" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="anthropic" name="Anthropic" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="internal" name="Internal GPU" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- OCR ---------- */}
        <TabsContent value="ocr" className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard index={0} title="Pages OCR'd" value="458,300" trend="+14%" icon={ScanText} />
            <KpiCard index={1} title="Printed Text Accuracy" value="99.6%" trend="+0.1%" icon={Target} />
            <KpiCard index={2} title="Handwriting Accuracy" value="94.9%" trend="+0.8%" icon={Target} />
            <KpiCard index={3} title="Avg OCR Time / Page" value="0.84s" trend="-0.06s" icon={Gauge} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>OCR Accuracy Trend</CardTitle>
              <CardDescription>Character-level accuracy on printed vs handwritten content.</CardDescription>
            </CardHeader>
            <CardContent className="h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ocrAccuracy} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis domain={[88, 100]} stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                  <Tooltip {...chartTooltipStyle} formatter={(value) => [`${value}%`, ""]} />
                  <Legend />
                  <Line type="monotone" dataKey="printed" name="Printed" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="handwritten" name="Handwritten" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- Extraction ---------- */}
        <TabsContent value="extraction" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Extraction Outcomes by Document Type</CardTitle>
              <CardDescription>Share of documents auto-approved, sent to review, or failed.</CardDescription>
            </CardHeader>
            <CardContent className="h-[360px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={extractionByType} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                  <XAxis type="number" domain={[0, 100]} stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                  <YAxis type="category" dataKey="name" width={80} stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip {...chartTooltipStyle} formatter={(value) => [`${value}%`, ""]} />
                  <Legend />
                  <Bar dataKey="success" name="Auto-approved" stackId="a" fill="#10b981" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="review" name="Human Review" stackId="a" fill="#f59e0b" />
                  <Bar dataKey="failed" name="Failed" stackId="a" fill="#ef4444" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- Organizations ---------- */}
        <TabsContent value="orgs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Usage by Organization</CardTitle>
              <CardDescription>Volume, cost and storage attribution per tenant.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {orgUsage.map((org) => (
                <div key={org.name} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 font-medium">
                      <Building2 className="w-4 h-4 text-muted-foreground" /> {org.name}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{org.docs.toLocaleString()} docs</span>
                      <span className="font-mono">{org.cost}</span>
                      <Badge variant="secondary" className="font-mono text-[10px]">{org.storage}</Badge>
                    </div>
                  </div>
                  <Progress value={org.pct} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ---------- Storage ---------- */}
        <TabsContent value="storage" className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard index={0} title="Total Storage" value="2.2 TB" trend="+140 GB" icon={Database} subtitle="of 5 TB quota" />
            <KpiCard index={1} title="Original Files" value="1.6 TB" icon={FileText} subtitle="73% of total" />
            <KpiCard index={2} title="Extracted JSON" value="410 GB" icon={Layers} subtitle="19% of total" />
            <KpiCard index={3} title="OCR Artifacts" value="190 GB" icon={ScanText} subtitle="8% of total" />
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Storage Growth</CardTitle>
              <CardDescription>Cumulative storage utilization (GB).</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={volumeData.map((d, i) => ({ name: d.name, gb: 1650 + i * 78 }))}
                  margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="gStorage" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip {...chartTooltipStyle} formatter={(value) => [`${value} GB`, "Storage"]} />
                  <Area type="monotone" dataKey="gb" name="Storage" stroke="#3b82f6" strokeWidth={2} fill="url(#gStorage)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
