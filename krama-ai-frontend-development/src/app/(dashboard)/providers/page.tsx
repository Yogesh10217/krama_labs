"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Network, KeyRound, Cpu, Activity, RefreshCw, Eye, EyeOff, CheckCircle2, AlertTriangle, Sliders, Zap } from "lucide-react";
import { AnalyticsHeader, KpiCard } from "@/features/analytics/components";
import { useProviders, useUpdateProviderRouting, useTestProviderConnection } from "@/hooks/use-providers";
import type { Provider } from "@/types";
import { cn } from "@/lib/utils";

export default function ProvidersPage() {
  const { data: providerData, isLoading } = useProviders();
  const updateRouting = useUpdateProviderRouting();
  const testConn = useTestProviderConnection();

  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [testResult, setTestResult] = useState<{ id: string; msg: string; latency: number } | null>(null);

  const handleTest = (providerId: string) => {
    testConn.mutate(providerId, {
      onSuccess: (res) => {
        setTestResult({ id: providerId, msg: res.message, latency: res.latencyMs });
        setTimeout(() => setTestResult(null), 5000);
      },
    });
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader
        title="AI Providers & Routing Engine"
        description="Manage LLM backends (OpenAI, Gemini, Anthropic, Ollama), routing weights, fallback failover, and API keys."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard index={0} title="Active Providers" value={String(providerData?.total ?? 4)} trend="All Operational" icon={Network} />
        <KpiCard index={1} title="Avg P95 Latency" value="430 ms" trend="-45ms" icon={Activity} />
        <KpiCard index={2} title="Provider Error Rate" value="0.02%" trend="-0.01%" icon={Zap} />
        <KpiCard index={3} title="Monthly LLM Cost" value="$2,950" icon={Cpu} subtitle="across all 4 clusters" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {isLoading ? (
          [1, 2, 3, 4].map((n) => <Card key={n} className="h-64 animate-pulse bg-muted/20" />)
        ) : (
          providerData?.items.map((prov, i) => (
            <motion.div
              key={prov.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="h-full flex flex-col glass hover:border-primary/40 transition-all duration-300">
                <CardHeader className="flex flex-row items-start justify-between pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-lg">
                      {prov.name[0]}
                    </div>
                    <div>
                      <CardTitle className="text-base font-semibold">{prov.name}</CardTitle>
                      <CardDescription className="text-xs font-mono">{prov.model}</CardDescription>
                    </div>
                  </div>
                  <Badge
                    variant={prov.status === "operational" ? "success" : prov.status === "degraded" ? "warning" : "destructive"}
                    className="capitalize"
                  >
                    {prov.status}
                  </Badge>
                </CardHeader>

                <CardContent className="flex-1 space-y-4 text-sm">
                  <div className="grid grid-cols-3 gap-2 bg-background/50 p-3 rounded-lg border text-center">
                    <div>
                      <p className="text-xs text-muted-foreground">P95 Latency</p>
                      <p className="font-mono font-bold">{prov.p95LatencyMs} ms</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Error Rate</p>
                      <p className="font-mono font-bold text-green-500">{prov.errorRate}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Spend (30d)</p>
                      <p className="font-mono font-bold">${prov.monthlySpendUsd.toFixed(2)}</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground font-medium">Traffic Routing Weight</span>
                      <span className="font-mono font-bold text-primary">{prov.routingWeight}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={prov.routingWeight}
                      onChange={(e) => updateRouting.mutate({ id: prov.id, weight: Number(e.target.value) })}
                      className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                  </div>

                  {testResult?.id === prov.id && (
                    <div className="p-2.5 rounded-md bg-primary/10 border border-primary/20 text-xs text-primary flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      <span>{testResult.msg}</span>
                    </div>
                  )}
                </CardContent>

                <CardFooter className="border-t bg-muted/10 py-3 flex items-center justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    onClick={() => setSelectedProvider(prov)}
                  >
                    <KeyRound className="w-3.5 h-3.5" /> API Keys
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-2 text-primary"
                    disabled={testConn.isPending && testConn.variables === prov.id}
                    onClick={() => handleTest(prov.id)}
                  >
                    <RefreshCw className={cn("w-3.5 h-3.5", testConn.isPending && testConn.variables === prov.id && "animate-spin")} />
                    Test Ping
                  </Button>
                </CardFooter>
              </Card>
            </motion.div>
          ))
        )}
      </div>

      {/* API Key Modal */}
      <Dialog open={!!selectedProvider} onOpenChange={(open) => !open && setSelectedProvider(null)}>
        <DialogContent className="glass-strong border-foreground/10 sm:max-w-[480px]">
          {selectedProvider && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <KeyRound className="w-5 h-5 text-primary" /> {selectedProvider.name} Credentials
                </DialogTitle>
                <DialogDescription>
                  Configure secret credentials used for LLM inference and extraction.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Secret API Key</Label>
                  <div className="relative">
                    <Input
                      type={showApiKey ? "text" : "password"}
                      placeholder="sk-proj-..."
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {selectedProvider.endpointUrl && (
                  <div className="space-y-2">
                    <Label>Custom Endpoint URL</Label>
                    <Input defaultValue={selectedProvider.endpointUrl} />
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setSelectedProvider(null)}>
                  Cancel
                </Button>
                <Button
                  className="ai-gradient-bg text-white"
                  onClick={() => {
                    setSelectedProvider(null);
                    setApiKeyInput("");
                  }}
                >
                  Save Secret Key
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
