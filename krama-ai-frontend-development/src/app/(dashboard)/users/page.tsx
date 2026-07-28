"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, UserPlus, MoreHorizontal, Shield, KeyRound, Ban, Users, Check, X, Lock, ShieldCheck, Mail } from "lucide-react";
import { AnalyticsHeader, KpiCard, ExportDialog } from "@/features/analytics/components";
import { useUsers, useInviteUser, useUpdateUserRole, useUpdateUserStatus, useRbacPermissions } from "@/hooks/use-users";
import type { UserRole } from "@/types";
import { cn } from "@/lib/utils";

const roleColors: Record<string, string> = {
  owner: "bg-primary/10 text-primary border-primary/20",
  admin: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  reviewer: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  analyst: "bg-muted text-muted-foreground border-border",
};

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [activeTab, setActiveTab] = useState("members");
  const [isInviteOpen, setIsInviteOpen] = useState(false);

  // Invite Form State
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState<UserRole>("reviewer");

  const { data: userData, isLoading } = useUsers({ search, role: roleFilter });
  const { data: rbacPermissions } = useRbacPermissions();
  const inviteUser = useInviteUser();
  const updateRole = useUpdateUserRole();
  const updateStatus = useUpdateUserStatus();

  const handleInviteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    inviteUser.mutate({ email: inviteEmail, name: inviteName, role: inviteRole });
    setInviteEmail("");
    setInviteName("");
    setIsInviteOpen(false);
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader title="User Management" description="Manage enterprise members, roles, permissions matrix, and MFA settings.">
        <ExportDialog label="Export Users" />
        <Dialog open={isInviteOpen} onOpenChange={setIsInviteOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 ai-gradient-bg border-0 text-white shadow-lg shadow-primary/20">
              <UserPlus className="w-4 h-4" /> Invite User
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-strong border-foreground/10 sm:max-w-[480px]">
            <form onSubmit={handleInviteSubmit}>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Mail className="w-5 h-5 text-primary" /> Invite Team Member
                </DialogTitle>
                <DialogDescription>
                  Send a workspace invite link with role-based permissions.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name (Optional)</Label>
                  <Input
                    id="name"
                    placeholder="e.g. Sarah Connor"
                    value={inviteName}
                    onChange={(e) => setInviteName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Assigned Role</Label>
                  <Select value={inviteRole} onValueChange={(val: any) => setInviteRole(val)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Admin — Full workspace control</SelectItem>
                      <SelectItem value="reviewer">Reviewer — Can approve & edit documents</SelectItem>
                      <SelectItem value="analyst">Analyst — Read-only document & report access</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" type="button" onClick={() => setIsInviteOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={inviteUser.isPending} className="ai-gradient-bg text-white">
                  {inviteUser.isPending ? "Sending..." : "Send Invitation"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </AnalyticsHeader>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard index={0} title="Total Members" value={String(userData?.total ?? 248)} trend="+12" icon={Users} />
        <KpiCard index={1} title="Active (30d)" value="214" trend="+8%" icon={Users} />
        <KpiCard index={2} title="Pending Invites" value="9" icon={UserPlus} />
        <KpiCard index={3} title="MFA Protection" value="92%" trend="+3%" icon={ShieldCheck} />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-muted/50 p-1 border">
          <TabsTrigger value="members" className="gap-2">
            <Users className="w-4 h-4" /> Workspace Members
          </TabsTrigger>
          <TabsTrigger value="rbac" className="gap-2">
            <Shield className="w-4 h-4" /> Role & Permissions Matrix
          </TabsTrigger>
        </TabsList>

        <TabsContent value="members" className="space-y-4">
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="overflow-hidden glass">
              <div className="p-4 border-b bg-muted/20 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 justify-between">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name or email..."
                    className="pl-9 bg-background"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <Select value={roleFilter} onValueChange={setRoleFilter}>
                  <SelectTrigger className="w-full sm:w-[160px] bg-background">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Roles</SelectItem>
                    <SelectItem value="owner">Owner</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="reviewer">Reviewer</SelectItem>
                    <SelectItem value="analyst">Analyst</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {isLoading ? (
                <div className="p-8 text-center text-muted-foreground">Loading members...</div>
              ) : (
                <Table>
                  <TableHeader className="bg-muted/40">
                    <TableRow>
                      <TableHead className="pl-6">User</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>MFA</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Active</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {userData?.items.map((user) => (
                      <TableRow key={user.id} className="hover:bg-muted/20 transition-colors">
                        <TableCell className="pl-6">
                          <div className="flex items-center gap-3">
                            <Avatar className="h-9 w-9 border border-primary/20">
                              <AvatarFallback className="text-xs bg-primary/10 text-primary font-bold">
                                {user.name.split(" ").map((n) => n[0]).join("")}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="text-sm font-medium">{user.name}</p>
                              <p className="text-xs text-muted-foreground font-mono">{user.email}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className={cn("text-xs font-semibold px-2.5 py-0.5 rounded-full border capitalize", roleColors[user.role])}>
                            {user.role}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{user.organizationName || "Apex Financial Global"}</TableCell>
                        <TableCell>
                          {user.mfaEnabled ? (
                            <Badge variant="outline" className="text-[10px] text-green-500 border-green-500/20 bg-green-500/10 gap-1">
                              <Check className="w-3 h-3" /> Enabled
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-[10px] text-muted-foreground gap-1">
                              Off
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={user.status === "active" ? "success" : user.status === "invited" ? "warning" : "destructive"}
                            className="capitalize"
                          >
                            {user.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{user.lastActiveAt || "—"}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48 glass-strong">
                              <DropdownMenuLabel>Role Action</DropdownMenuLabel>
                              <DropdownMenuItem
                                onClick={() => updateRole.mutate({ userId: user.id, role: "admin" })}
                                className="gap-2 cursor-pointer"
                              >
                                Make Admin
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => updateRole.mutate({ userId: user.id, role: "reviewer" })}
                                className="gap-2 cursor-pointer"
                              >
                                Make Reviewer
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              {user.status === "suspended" ? (
                                <DropdownMenuItem
                                  onClick={() => updateStatus.mutate({ userId: user.id, status: "active" })}
                                  className="gap-2 text-green-500 focus:text-green-500 cursor-pointer"
                                >
                                  Re-Activate Member
                                </DropdownMenuItem>
                              ) : (
                                <DropdownMenuItem
                                  onClick={() => updateStatus.mutate({ userId: user.id, status: "suspended" })}
                                  className="gap-2 text-destructive focus:text-destructive cursor-pointer"
                                >
                                  <Ban className="w-4 h-4" /> Suspend Member
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Card>
          </motion.div>
        </TabsContent>

        <TabsContent value="rbac" className="space-y-4">
          <Card className="p-6 glass space-y-4">
            <div>
              <h3 className="text-base font-semibold">Role-Based Access Control (RBAC) Matrix</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Overview of default enterprise security permissions assigned per role.
              </p>
            </div>

            <Table>
              <TableHeader className="bg-muted/40">
                <TableRow>
                  <TableHead className="w-[300px]">Permission Feature</TableHead>
                  <TableHead className="text-center">Owner</TableHead>
                  <TableHead className="text-center">Admin</TableHead>
                  <TableHead className="text-center">Reviewer</TableHead>
                  <TableHead className="text-center">Analyst</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rbacPermissions?.map((perm) => (
                  <TableRow key={perm.id} className="hover:bg-muted/20">
                    <TableCell>
                      <p className="text-sm font-medium">{perm.name}</p>
                      <p className="text-xs text-muted-foreground">{perm.description}</p>
                    </TableCell>
                    <TableCell className="text-center">
                      <Check className="w-4 h-4 text-green-500 mx-auto" />
                    </TableCell>
                    <TableCell className="text-center">
                      {perm.admin ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : <X className="w-4 h-4 text-muted-foreground/40 mx-auto" />}
                    </TableCell>
                    <TableCell className="text-center">
                      {perm.reviewer ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : <X className="w-4 h-4 text-muted-foreground/40 mx-auto" />}
                    </TableCell>
                    <TableCell className="text-center">
                      {perm.analyst ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : <X className="w-4 h-4 text-muted-foreground/40 mx-auto" />}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
