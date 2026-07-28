"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { User, Building2, Shield, KeyRound, Bell, Sliders, ScrollText, Flag, Laptop, CheckCircle2, Copy, Plus, Trash2 } from "lucide-react";
import { AnalyticsHeader } from "@/features/analytics/components";
import { useAuditLogs, useFeatureFlags, useToggleFeatureFlag } from "@/hooks/use-audit";
import { CURRENT_USER } from "@/config/navigation";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");
  const { data: auditLogs } = useAuditLogs();
  const { data: featureFlags } = useFeatureFlags();
  const toggleFlag = useToggleFeatureFlag();

  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);

  const handleCopyKey = (key: string, id: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKeyId(id);
    setTimeout(() => setCopiedKeyId(null), 2500);
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader title="System Settings" description="Account preferences, security parameters, API secret keys, feature flags, and audit trails." />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-muted/40 p-1 border grid grid-cols-2 md:grid-cols-6 gap-1">
          <TabsTrigger value="general" className="gap-2 text-xs">
            <User className="w-3.5 h-3.5" /> Profile
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2 text-xs">
            <Shield className="w-3.5 h-3.5" /> Security
          </TabsTrigger>
          <TabsTrigger value="api" className="gap-2 text-xs">
            <KeyRound className="w-3.5 h-3.5" /> API Keys
          </TabsTrigger>
          <TabsTrigger value="flags" className="gap-2 text-xs">
            <Flag className="w-3.5 h-3.5" /> Feature Flags
          </TabsTrigger>
          <TabsTrigger value="audit" className="gap-2 text-xs">
            <ScrollText className="w-3.5 h-3.5" /> Audit Logs
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2 text-xs">
            <Bell className="w-3.5 h-3.5" /> Notifications
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="general" className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-base">User Profile</CardTitle>
              <CardDescription>Update your personal information and profile picture.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input id="name" defaultValue={CURRENT_USER.name} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input id="email" defaultValue={CURRENT_USER.email} disabled />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Assigned Role</Label>
                <Input defaultValue={CURRENT_USER.role} disabled className="max-w-md font-mono" />
              </div>
            </CardContent>
            <CardFooter className="border-t bg-muted/10 py-3 justify-end">
              <Button className="ai-gradient-bg text-white">Save Changes</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-base">Multi-Factor Authentication (MFA)</CardTitle>
              <CardDescription>Require TOTP authenticator app tokens for login.</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Authenticator App (TOTP)</p>
                <p className="text-xs text-muted-foreground">Configured via Google Authenticator or 1Password</p>
              </div>
              <Badge variant="outline" className="text-green-500 border-green-500/20 bg-green-500/10">Active</Badge>
            </CardContent>
          </Card>

          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-base">Active Sessions</CardTitle>
              <CardDescription>Devices currently authenticated to your account.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg border bg-background/50">
                  <div className="flex items-center gap-3">
                    <Laptop className="w-5 h-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">MacBook Pro · Chrome 126</p>
                      <p className="text-xs text-muted-foreground">192.168.1.104 · Current Session</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">Active Now</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api" className="space-y-6">
          <Card className="glass">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">Secret API Keys</CardTitle>
                <CardDescription>Authenticate programmatically with the Krama AI FastAPI service.</CardDescription>
              </div>
              <Button size="sm" className="gap-2 ai-gradient-bg text-white">
                <Plus className="w-4 h-4" /> Create API Key
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    <TableHead>Key Name</TableHead>
                    <TableHead>Key Prefix</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Used</TableHead>
                    <TableHead className="w-[80px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium text-sm">Production Backend Key</TableCell>
                    <TableCell className="font-mono text-xs text-primary">krama_live_9f82...x3k</TableCell>
                    <TableCell className="text-xs text-muted-foreground">Jul 12, 2024</TableCell>
                    <TableCell className="text-xs text-muted-foreground">2 mins ago</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        onClick={() => handleCopyKey("krama_live_9f82901823901823x3k", "k1")}
                      >
                        {copiedKeyId === "k1" ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Feature Flags Tab */}
        <TabsContent value="flags" className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-base">Enterprise Feature Flags</CardTitle>
              <CardDescription>Toggle experimental algorithms and processing rules in real time.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {featureFlags?.map((flag) => (
                <div key={flag.key} className="flex items-center justify-between p-4 rounded-xl border bg-background/50">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold">{flag.name}</p>
                      <Badge variant="outline" className="text-[10px] uppercase font-mono">{flag.category}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{flag.description}</p>
                  </div>
                  <button
                    onClick={() => toggleFlag.mutate({ key: flag.key, enabled: !flag.enabled })}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      flag.enabled ? "bg-primary" : "bg-muted"
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                        flag.enabled ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Logs Tab */}
        <TabsContent value="audit" className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-base">System Audit Trail</CardTitle>
              <CardDescription>Immutable record of security events and administrative actions.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Actor</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>IP Address</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {auditLogs?.items.map((log) => (
                    <TableRow key={log.id} className="hover:bg-muted/20 text-xs font-mono">
                      <TableCell className="text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString()}</TableCell>
                      <TableCell className="font-sans font-medium text-foreground">{log.actor.name}</TableCell>
                      <TableCell className="text-primary font-bold">{log.action}</TableCell>
                      <TableCell className="font-sans text-muted-foreground">{log.target}</TableCell>
                      <TableCell className="text-muted-foreground">{log.ipAddress}</TableCell>
                      <TableCell>
                        <Badge variant={log.status === "success" ? "success" : "destructive"} className="capitalize text-[10px]">
                          {log.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-base">Alert Preferences</CardTitle>
              <CardDescription>Configure webhook thresholds and email dispatch schedules.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg border bg-background/50">
                <div>
                  <p className="text-sm font-medium">Low Confidence Alerts</p>
                  <p className="text-xs text-muted-foreground">Notify when document confidence drops below 80%</p>
                </div>
                <Badge variant="outline" className="text-xs">Email + In-App</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
