"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { HeartPulse, Database, Server, Cpu, HardDrive, Zap, RefreshCw, CheckCircle2, AlertTriangle, Activity, ShieldCheck } from "lucide-react";
import { AnalyticsHeader, KpiCard } from "@/features/analytics/components";
import { useSystemHealth, useTriggerHealthCheck } from "@/hooks/use-health";
import { cn } from "@/lib/utils";

const typeIcons = {
  redis: Database,
  postgres: Database,
  queue: Server,
  worker: Cpu,
  api: Zap,
  storage: HardDrive,
};

export default function SystemHealthPage() {
  const { data: healthServices, isLoading, refetch, isRefetching } = useSystemHealth();
  const triggerCheck = useTriggerHealthCheck();

  const handleManualCheck = () => {
    triggerCheck.mutate();
    refetch();
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader
        title="Production System Health"
        description="Real-time telemetry, queue backpressure, worker pool utilization, and database connection metrics."
      >
        <Button
          variant="outline"
          className="gap-2 border-primary/20 hover:bg-primary/10"
          onClick={handleManualCheck}
          disabled={isRefetching || triggerCheck.isPending}
        >
          <RefreshCw className={cn("w-4 h-4 text-primary", (isRefetching || triggerCheck.isPending) && "animate-spin")} />
          Run Health Diagnostics
        </Button>
      </AnalyticsHeader>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard index={0} title="Overall Status" value="99.98%" trend="Operational" icon={HeartPulse} />
        <KpiCard index={1} title="Active Worker Pool" value="32 Nodes" trend="Autoscaling" icon={Cpu} />
        <KpiCard index={2} title="Redis Queue Backlog" value="42 Jobs" trend="-15" icon={Server} />
        <KpiCard index={3} title="DB Connection Pool" value="64 / 100" icon={Database} subtitle="Latency 4.8ms" />
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight">Monitored Infrastructure & Services</h2>
          <span className="text-xs text-muted-foreground font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-ping" />
            Live Polling (Every 10s)
          </span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <Card key={n} className="h-56 animate-pulse bg-muted/20" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {healthServices?.map((svc, i) => {
              const Icon = typeIcons[svc.type] || Activity;
              return (
                <motion.div
                  key={svc.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="h-full glass hover:border-primary/40 transition-all duration-300 flex flex-col justify-between">
                    <CardHeader className="flex flex-row items-start justify-between pb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold">{svc.name}</CardTitle>
                          <CardDescription className="text-xs font-mono">Uptime: {svc.uptimePct}%</CardDescription>
                        </div>
                      </div>
                      <Badge
                        variant={svc.status === "healthy" ? "success" : svc.status === "degraded" ? "warning" : "destructive"}
                        className="capitalize text-[10px]"
                      >
                        {svc.status}
                      </Badge>
                    </CardHeader>

                    <CardContent className="space-y-4">
                      <p className="text-xs text-muted-foreground leading-relaxed">{svc.details}</p>

                      <div className="space-y-2 pt-2 border-t border-foreground/5">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-muted-foreground">Response Latency</span>
                          <span className="font-bold text-foreground">{svc.latencyMs} ms</span>
                        </div>

                        {svc.metrics.cpuPct !== undefined && (
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>CPU Load</span>
                              <span>{svc.metrics.cpuPct}%</span>
                            </div>
                            <Progress value={svc.metrics.cpuPct} className="h-1.5" />
                          </div>
                        )}

                        {svc.metrics.memoryPct !== undefined && (
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs text-muted-foreground">
                              <span>Memory Consumption</span>
                              <span>{svc.metrics.memoryPct}%</span>
                            </div>
                            <Progress value={svc.metrics.memoryPct} className="h-1.5" />
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
