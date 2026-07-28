"use client";

import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ArrowDownRight, ArrowUpRight, Download, FileSpreadsheet, FileText, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ComponentType } from "react";

/* ---------------------------------- KPI Card ---------------------------------- */

export interface KpiCardProps {
  title: string;
  value: string;
  trend?: string;
  trendPositive?: boolean;
  icon: ComponentType<any>;
  subtitle?: string;
  index?: number;
}

const kpiVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, type: "spring", stiffness: 300, damping: 24 },
  }),
};

export function KpiCard({ title, value, trend, trendPositive = true, icon: Icon, subtitle, index = 0 }: KpiCardProps) {
  return (
    <motion.div variants={kpiVariants} initial="hidden" animate="show" custom={index}>
      <Card className="hover:border-primary/30 transition-colors shadow-sm bg-card/50 backdrop-blur h-full">
        <CardContent className="p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-secondary rounded-lg">
              <Icon className="w-4 h-4 text-primary" />
            </div>
            {trend && (
              <Badge
                variant={trendPositive ? "success" : "destructive"}
                className="flex items-center gap-1 font-mono text-[10px]"
              >
                {trendPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {trend}
              </Badge>
            )}
          </div>
          <h3 className="text-xs font-medium text-muted-foreground mb-1">{title}</h3>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
        </CardContent>
      </Card>
    </motion.div>
  );
}

/* -------------------------------- Export Dialog ------------------------------- */

export function ExportDialog({ label = "Export" }: { label?: string }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Download className="w-4 h-4" /> {label}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[440px]">
        <DialogHeader>
          <DialogTitle>Export Data</DialogTitle>
          <DialogDescription>
            Configure the format and range for your data export.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-5 py-2">
          <div className="space-y-2">
            <Label>Format</Label>
            <div className="grid grid-cols-2 gap-3">
              <button className="flex items-center gap-3 rounded-lg border p-3 hover:border-primary hover:bg-primary/5 transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <FileSpreadsheet className="w-5 h-5 text-green-500" />
                <div>
                  <p className="text-sm font-medium">CSV</p>
                  <p className="text-[10px] text-muted-foreground">Spreadsheet</p>
                </div>
              </button>
              <button className="flex items-center gap-3 rounded-lg border p-3 hover:border-primary hover:bg-primary/5 transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <FileText className="w-5 h-5 text-red-500" />
                <div>
                  <p className="text-sm font-medium">PDF</p>
                  <p className="text-[10px] text-muted-foreground">Report</p>
                </div>
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Date Range</Label>
            <Select defaultValue="30d">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last quarter</SelectItem>
                <SelectItem value="1y">Last 12 months</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="includeRaw" defaultChecked />
            <Label htmlFor="includeRaw" className="text-sm font-normal text-muted-foreground">
              Include raw event data
            </Label>
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button className="gap-2">
            <Download className="w-4 h-4" /> Export
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* ------------------------------- Range Filter --------------------------------- */

export function RangeFilter() {
  return (
    <div className="flex items-center gap-2">
      <Select defaultValue="30d">
        <SelectTrigger className="w-[160px] bg-background">
          <Calendar className="w-4 h-4 mr-2 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="24h">Last 24 hours</SelectItem>
          <SelectItem value="7d">Last 7 days</SelectItem>
          <SelectItem value="30d">Last 30 days</SelectItem>
          <SelectItem value="90d">Last quarter</SelectItem>
        </SelectContent>
      </Select>
      <Select defaultValue="all">
        <SelectTrigger className="w-[180px] bg-background">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Organizations</SelectItem>
          <SelectItem value="acme">Acme Corporation</SelectItem>
          <SelectItem value="globex">Globex Inc</SelectItem>
          <SelectItem value="soylent">Soylent Corp</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

/* ------------------------------- Chart Tooltip -------------------------------- */

export const chartTooltipStyle = {
  contentStyle: {
    backgroundColor: "hsl(var(--popover))",
    border: "1px solid hsl(var(--border))",
    borderRadius: "8px",
    fontSize: "12px",
  },
  itemStyle: { color: "hsl(var(--foreground))" },
};

/* ------------------------------- Page Header ----------------------------------- */
/**
 * @deprecated Use `PageHeader` from `@/components/shared/page` directly.
 * Re-exported here so existing analytics pages keep a single implementation.
 */
export { PageHeader as AnalyticsHeader } from "@/components/shared/page";
