"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, RefreshCw, ServerCog, Loader2, CheckCircle2, XCircle, PauseCircle } from "lucide-react";
import { AnalyticsHeader, KpiCard } from "@/features/analytics/components";

const jobs = [
  { id: "job_991", type: "Batch Extraction", org: "Apex Financial Global", docs: 512, progress: 74, status: "running", started: "10:12 UTC", eta: "14m" },
  { id: "job_992", type: "Entity Linking", org: "Apex Financial Global", docs: 128, progress: 31, status: "running", started: "10:48 UTC", eta: "26m" },
  { id: "job_989", type: "OCR Reprocess", org: "Nexus Healthcare Group", docs: 2048, progress: 100, status: "completed", started: "08:20 UTC", eta: "—" },
  { id: "job_986", type: "Batch Extraction", org: "Vertex Global Logistics", docs: 64, progress: 100, status: "completed", started: "07:44 UTC", eta: "—" },
  { id: "job_984", type: "Schema Migration", org: "Horizon Insurance Systems", docs: 320, progress: 12, status: "paused", started: "06:10 UTC", eta: "—" },
  { id: "job_981", type: "Batch Extraction", org: "Nexus Healthcare Group", docs: 96, progress: 44, status: "failed", started: "05:52 UTC", eta: "—" },
];

const statusConfig = {
  running: { icon: Loader2, variant: "warning" as const, spin: true },
  completed: { icon: CheckCircle2, variant: "success" as const, spin: false },
  paused: { icon: PauseCircle, variant: "secondary" as const, spin: false },
  failed: { icon: XCircle, variant: "destructive" as const, spin: false },
};

export default function JobsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const filtered = jobs.filter((job) => {
    const matchesSearch =
      job.id.toLowerCase().includes(search.toLowerCase()) ||
      job.type.toLowerCase().includes(search.toLowerCase()) ||
      job.org.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = status === "all" || job.status === status;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader title="Jobs" description="Monitor asynchronous processing jobs across all pipelines.">
        <Button variant="outline" className="gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </AnalyticsHeader>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard index={0} title="Active Jobs" value="2" icon={ServerCog} />
        <KpiCard index={1} title="Completed (24h)" value="184" trend="+9%" icon={CheckCircle2} />
        <KpiCard index={2} title="Failed (24h)" value="3" trend="-2" icon={XCircle} />
        <KpiCard index={3} title="Avg Job Duration" value="8m 24s" trend="-14%" icon={Loader2} />
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card className="overflow-hidden">
          <div className="p-4 border-b bg-muted/20 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search jobs by ID, type, or organization..."
                className="pl-9 bg-background"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-full sm:w-[160px] bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead className="pl-6">Job</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead>Documents</TableHead>
                <TableHead className="w-[220px]">Progress</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>ETA</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((job) => {
                const config = statusConfig[job.status as keyof typeof statusConfig];
                const StatusIcon = config.icon;
                return (
                  <TableRow key={job.id}>
                    <TableCell className="pl-6">
                      <div>
                        <p className="text-sm font-medium">{job.type}</p>
                        <p className="text-xs text-muted-foreground font-mono mt-0.5">{job.id}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{job.org}</TableCell>
                    <TableCell className="text-sm font-mono">{job.docs.toLocaleString()}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={job.progress}
                          className={
                            job.status === "failed" ? "h-1.5 flex-1 [&>div]:bg-destructive" :
                            job.status === "completed" ? "h-1.5 flex-1 [&>div]:bg-green-500" : "h-1.5 flex-1"
                          }
                        />
                        <span className="text-xs font-mono w-9 text-right">{job.progress}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={config.variant} className="capitalize gap-1">
                        <StatusIcon className={config.spin ? "w-3 h-3 animate-spin" : "w-3 h-3"} />
                        {job.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">{job.started}</TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">{job.eta}</TableCell>
                  </TableRow>
                );
              })}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="h-40 text-center text-muted-foreground">
                    No jobs found matching your filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      </motion.div>
    </div>
  );
}
