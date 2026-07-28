"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FilePieChart, Clock, Plus, Download, CalendarClock, FileSpreadsheet, FileText } from "lucide-react";
import { ExportDialog, AnalyticsHeader } from "@/features/analytics/components";

const scheduledReports = [
  { id: "rep_1", name: "Monthly Claims Adjudication & Fraud Audit", cadence: "Monthly · 1st, 08:00 UTC", recipients: 6, format: "PDF", lastRun: "Oct 1, 2024" },
  { id: "rep_2", name: "Hospital Tariff & Deduction Breakdown", cadence: "Weekly · Mon, 06:00 UTC", recipients: 4, format: "CSV", lastRun: "Oct 21, 2024" },
  { id: "rep_3", name: "IRDAI SLA & Pre-Auth Compliance", cadence: "Weekly · Fri, 17:00 UTC", recipients: 8, format: "PDF", lastRun: "Oct 18, 2024" },
];

const recentReports = [
  { id: "run_991", name: "Monthly Claims Adjudication — October", generated: "Oct 1, 2024 08:01 UTC", size: "4.1 MB", format: "PDF", status: "ready" },
  { id: "run_990", name: "Hospital Tariff & Room Rent Deductions — W43", generated: "Oct 21, 2024 06:00 UTC", size: "820 KB", format: "CSV", status: "ready" },
  { id: "run_989", name: "IRDAI Pre-Auth Turnaround SLA — W42", generated: "Oct 18, 2024 17:02 UTC", size: "2.7 MB", format: "PDF", status: "ready" },
  { id: "run_988", name: "Ad-hoc: Motor Repair Estimate Anomaly Audit", generated: "Oct 16, 2024 11:34 UTC", size: "1.4 MB", format: "CSV", status: "ready" },
];

export default function ReportsPage() {
  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1400px] mx-auto pb-20">
      <AnalyticsHeader title="Reports" description="Schedule, generate, and download enterprise reports.">
        <ExportDialog label="Generate Report" />
        <Button className="gap-2">
          <Plus className="w-4 h-4" /> New Schedule
        </Button>
      </AnalyticsHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scheduled Reports */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1 space-y-4"
        >
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <CalendarClock className="w-4 h-4" /> Scheduled
          </h2>
          {scheduledReports.map((report, i) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
            >
              <Card className="hover:border-primary/40 transition-colors group cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="p-2 bg-primary/10 text-primary rounded-lg shrink-0">
                      <FilePieChart className="w-4 h-4" />
                    </div>
                    <Badge variant="outline" className="font-mono text-[10px]">{report.format}</Badge>
                  </div>
                  <h3 className="font-medium text-sm mt-3 group-hover:text-primary transition-colors">{report.name}</h3>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {report.cadence}
                  </p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t text-xs text-muted-foreground">
                    <span>{report.recipients} recipients</span>
                    <span>Last run {report.lastRun}</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Recent Reports */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle>Generated Reports</CardTitle>
              <CardDescription>Download previously generated report artifacts.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>Report</TableHead>
                    <TableHead>Generated</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right pr-6">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentReports.map((report) => (
                    <TableRow key={report.id} className="group">
                      <TableCell>
                        <div className="flex items-center gap-3 pl-2">
                          {report.format === "CSV" ? (
                            <FileSpreadsheet className="w-4 h-4 text-green-500 shrink-0" />
                          ) : (
                            <FileText className="w-4 h-4 text-red-500 shrink-0" />
                          )}
                          <span className="text-sm font-medium">{report.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">{report.generated}</TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">{report.size}</TableCell>
                      <TableCell>
                        <Badge variant={report.status === "ready" ? "success" : "warning"} className="capitalize">
                          {report.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right pr-4">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity"
                          disabled={report.status !== "ready"}
                        >
                          <Download className="w-3.5 h-3.5" /> Download
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
