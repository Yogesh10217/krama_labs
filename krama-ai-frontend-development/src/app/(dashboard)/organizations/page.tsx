"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Building2, Plus, Users, FileText, HardDrive, ChevronRight, Globe, Search, ShieldCheck, CheckCircle2, Sliders, ExternalLink } from "lucide-react";
import { AnalyticsHeader, KpiCard } from "@/features/analytics/components";
import { useOrganizations, useCreateOrganization, useUpdateOrganization } from "@/hooks/use-organizations";
import type { Organization } from "@/types";
import { cn } from "@/lib/utils";

const planColors: Record<string, string> = {
  enterprise: "bg-primary/10 text-primary border-primary/20",
  pro: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  startup: "bg-blue-500/10 text-blue-500 border-blue-500/20",
};

export default function OrganizationsPage() {
  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("all");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);

  // Form state
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgDomain, setNewOrgDomain] = useState("");
  const [newOrgPlan, setNewOrgPlan] = useState<"startup" | "pro" | "enterprise">("startup");

  const { data: orgData, isLoading } = useOrganizations({ search, plan: planFilter });
  const createOrg = useCreateOrganization();
  const updateOrg = useUpdateOrganization();

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    createOrg.mutate({
      name: newOrgName,
      domain: newOrgDomain || `${newOrgName.toLowerCase().replace(/\s+/g, "")}.com`,
      plan: newOrgPlan,
    });
    setNewOrgName("");
    setNewOrgDomain("");
    setIsCreateOpen(false);
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1e12) return `${(bytes / 1e12).toFixed(1)} TB`;
    if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(0)} GB`;
    return `${(bytes / 1e6).toFixed(0)} MB`;
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader title="Organizations" description="Manage multi-tenant workspaces, enterprise quotas, and domain routing.">
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 ai-gradient-bg border-0 text-white shadow-lg shadow-primary/20">
              <Plus className="w-4 h-4" /> New Organization
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-strong border-foreground/10 sm:max-w-[480px]">
            <form onSubmit={handleCreateSubmit}>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-primary" /> Create Workspace
                </DialogTitle>
                <DialogDescription>
                  Set up a new isolated organization tenant for your team or customer.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Organization Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g. Nexus Dynamics"
                    value={newOrgName}
                    onChange={(e) => setNewOrgName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="domain">Primary Domain</Label>
                  <Input
                    id="domain"
                    placeholder="e.g. nexus.com"
                    value={newOrgDomain}
                    onChange={(e) => setNewOrgDomain(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Subscription Plan</Label>
                  <Select value={newOrgPlan} onValueChange={(val: any) => setNewOrgPlan(val)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="startup">Startup Tier (500 GB Storage)</SelectItem>
                      <SelectItem value="pro">Pro Tier (1.0 TB Storage)</SelectItem>
                      <SelectItem value="enterprise">Enterprise Tier (2.0 TB+ Dedicated)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createOrg.isPending} className="ai-gradient-bg text-white">
                  {createOrg.isPending ? "Creating..." : "Create Tenant"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </AnalyticsHeader>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard index={0} title="Total Workspaces" value={String(orgData?.total ?? 4)} trend="+1" icon={Building2} />
        <KpiCard index={1} title="Active Members" value="248" trend="+12" icon={Users} />
        <KpiCard index={2} title="Docs Processed" value="144.5K" trend="+11%" icon={FileText} />
        <KpiCard index={3} title="Total Storage" value="2.2 TB" icon={HardDrive} subtitle="across all active tenants" />
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-muted/20 p-3 rounded-xl border">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Filter organizations by name or domain..."
            className="pl-9 bg-background"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Select value={planFilter} onValueChange={setPlanFilter}>
            <SelectTrigger className="w-[160px] bg-background">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Plans</SelectItem>
              <SelectItem value="enterprise">Enterprise</SelectItem>
              <SelectItem value="pro">Pro</SelectItem>
              <SelectItem value="startup">Startup</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((n) => (
            <Card key={n} className="h-[220px] animate-pulse bg-muted/20" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {orgData?.items.map((org, i) => {
            const usagePct = Math.round((org.storageUsedBytes / org.storageQuotaBytes) * 100);
            return (
              <motion.div
                key={org.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i }}
              >
                <Card className="h-full flex flex-col hover:border-primary/40 transition-all duration-300 glass group">
                  <CardHeader className="flex flex-row items-start justify-between pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center border border-primary/20">
                        <Building2 className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold group-hover:text-primary transition-colors flex items-center gap-2">
                          {org.name}
                        </h3>
                        <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Globe className="w-3 h-3 text-primary/70" /> {org.domain}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full border capitalize", planColors[org.plan])}>
                        {org.plan}
                      </span>
                      <Badge
                        variant={org.status === "active" ? "success" : org.status === "trial" ? "warning" : "destructive"}
                        className="capitalize text-[10px]"
                      >
                        {org.status.replace("_", " ")}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="flex-1 space-y-4">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-background/50 rounded-lg p-3 text-center border">
                        <p className="text-lg font-bold">{org.memberCount}</p>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Members</p>
                      </div>
                      <div className="bg-background/50 rounded-lg p-3 text-center border">
                        <p className="text-lg font-bold">{(org.documentCount / 1000).toFixed(1)}K</p>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Documents</p>
                      </div>
                      <div className="bg-background/50 rounded-lg p-3 text-center border">
                        <p className="text-lg font-bold">{usagePct}%</p>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Storage</p>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Storage quota</span>
                        <span className="font-mono text-foreground font-medium">
                          {formatBytes(org.storageUsedBytes)} / {formatBytes(org.storageQuotaBytes)}
                        </span>
                      </div>
                      <Progress value={usagePct} className="h-1.5" />
                    </div>
                  </CardContent>

                  <CardFooter className="border-t bg-muted/10 py-3 justify-between">
                    <span className="text-xs text-muted-foreground font-mono">{org.id}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-1 text-primary hover:text-primary hover:bg-primary/10"
                      onClick={() => setSelectedOrg(org)}
                    >
                      Manage <ChevronRight className="w-4 h-4" />
                    </Button>
                  </CardFooter>
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Organization Details Modal */}
      <Dialog open={!!selectedOrg} onOpenChange={(open) => !open && setSelectedOrg(null)}>
        <DialogContent className="glass-strong border-foreground/10 sm:max-w-[640px]">
          {selectedOrg && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
                      <Building2 className="w-5 h-5" />
                    </div>
                    <div>
                      <DialogTitle className="text-lg">{selectedOrg.name}</DialogTitle>
                      <DialogDescription className="text-xs flex items-center gap-1 mt-0.5">
                        <Globe className="w-3 h-3" /> {selectedOrg.domain} · {selectedOrg.id}
                      </DialogDescription>
                    </div>
                  </div>
                  <Badge variant={selectedOrg.status === "active" ? "success" : "warning"}>
                    {selectedOrg.status}
                  </Badge>
                </div>
              </DialogHeader>

              <Tabs defaultValue="overview" className="mt-4">
                <TabsList className="grid grid-cols-3 bg-muted/50">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="quota">Storage & Quotas</TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-background/60 p-4 rounded-xl border space-y-1">
                      <p className="text-xs text-muted-foreground">Current Plan</p>
                      <p className="text-base font-semibold capitalize">{selectedOrg.plan} Tier</p>
                    </div>
                    <div className="bg-background/60 p-4 rounded-xl border space-y-1">
                      <p className="text-xs text-muted-foreground">Member Seats</p>
                      <p className="text-base font-semibold">{selectedOrg.memberCount} seats occupied</p>
                    </div>
                    <div className="bg-background/60 p-4 rounded-xl border space-y-1">
                      <p className="text-xs text-muted-foreground">Document Count</p>
                      <p className="text-base font-semibold">{selectedOrg.documentCount.toLocaleString()} total</p>
                    </div>
                    <div className="bg-background/60 p-4 rounded-xl border space-y-1">
                      <p className="text-xs text-muted-foreground">Created On</p>
                      <p className="text-base font-semibold">{new Date(selectedOrg.createdAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="quota" className="space-y-4 pt-4">
                  <div className="space-y-2 bg-background/60 p-4 rounded-xl border">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">Storage Used</span>
                      <span className="font-mono text-primary font-bold">
                        {formatBytes(selectedOrg.storageUsedBytes)} / {formatBytes(selectedOrg.storageQuotaBytes)}
                      </span>
                    </div>
                    <Progress value={(selectedOrg.storageUsedBytes / selectedOrg.storageQuotaBytes) * 100} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-2">
                      Need more storage? Upgrade to Enterprise for unlimited blob storage.
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="settings" className="space-y-4 pt-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-lg border bg-background/50">
                      <div>
                        <p className="text-sm font-medium">SSO Single Sign-On</p>
                        <p className="text-xs text-muted-foreground">Enforce SAML 2.0 / Okta authentication</p>
                      </div>
                      <Badge variant="outline" className="text-xs">Enabled</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg border bg-background/50">
                      <div>
                        <p className="text-sm font-medium">Auto-Redaction Policy</p>
                        <p className="text-xs text-muted-foreground">Redact SSNs & PII on ingest</p>
                      </div>
                      <Badge variant="outline" className="text-xs">Active</Badge>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter className="mt-6">
                <Button variant="outline" onClick={() => setSelectedOrg(null)}>
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
