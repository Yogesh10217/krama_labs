"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CheckCircle2, XCircle, Search, Filter, AlertCircle, FileText, ArrowRight, Activity, Clock } from "lucide-react";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { EmptyState } from "@/components/shared/states";

const reviewQueue = [
  { id: "DOC-8922", name: "Invoice_XCorp_Q3.pdf", model: "Invoice Pro", confidence: "74%", priority: "High", waitTime: "2h 14m", errors: 2 },
  { id: "DOC-8924", name: "Employee_Contract_JSmith.docx", model: "Legal Eagle", confidence: "68%", priority: "Medium", waitTime: "5h 22m", errors: 1 },
  { id: "DOC-8925", name: "Tax_Return_2023_Acme.pdf", model: "Extract v2", confidence: "45%", priority: "High", waitTime: "1h 10m", errors: 5 },
  { id: "DOC-8928", name: "Receipt_Scan_Travel.jpg", model: "Invoice Pro", confidence: "81%", priority: "Low", waitTime: "12h 45m", errors: 1 },
  { id: "DOC-8931", name: "MSA_Globex_Draft.pdf", model: "Legal Eagle", confidence: "52%", priority: "High", waitTime: "45m", errors: 3 },
];

export default function ReviewQueuePage() {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredQueue = reviewQueue.filter(doc => 
    doc.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    doc.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-[1600px] mx-auto h-full flex flex-col">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Human Review</h1>
          <p className="text-muted-foreground mt-1">Resolve low-confidence extractions and validation errors.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="gap-2">
            <Filter className="w-4 h-4" /> Filter Queue
          </Button>
          <Button className="gap-2">
            <Activity className="w-4 h-4" /> Start Review Session
          </Button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="md:col-span-1 space-y-6"
        >
          <Card className="bg-primary/5 border-primary/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Queue Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-4xl font-bold tracking-tight text-primary">{reviewQueue.length}</p>
                <p className="text-sm text-muted-foreground mt-1">Documents pending review</p>
              </div>
              <div className="space-y-2 pt-4 border-t border-primary/10">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">High Priority</span>
                  <span className="font-medium text-destructive">3</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Average Wait Time</span>
                  <span className="font-medium">4h 12m</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">SLA Breaches</span>
                  <span className="font-medium">0</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Reviewer Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>1. Verify low-confidence fields marked in yellow or red.</p>
              <p>2. Fix structural errors reported by the validation engine.</p>
              <p>3. If the document is illegible, reject it with a clear reason.</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="md:col-span-3 glass lift rounded-xl flex flex-col overflow-hidden"
        >
          <div className="p-4 border-b bg-muted/20 flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                placeholder="Search queue by ID or name..." 
                className="pl-9 bg-background"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="flex-1 overflow-auto custom-scrollbar">
            <Table>
              <TableHeader className="bg-muted/50 sticky top-0 z-10 backdrop-blur-sm">
                <TableRow>
                  <TableHead className="w-[300px]">Document</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Errors</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Wait Time</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredQueue.map((doc) => (
                  <TableRow key={doc.id} className="group cursor-pointer hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-primary/10 text-primary flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="overflow-hidden">
                          <p className="font-medium truncate text-sm">{doc.name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-muted-foreground">{doc.id}</span>
                            <span className="text-[10px] bg-secondary px-1.5 py-0.5 rounded text-secondary-foreground">
                              {doc.model}
                            </span>
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={parseInt(doc.confidence) > 70 ? "warning" : "destructive"}>
                        {doc.confidence}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5 text-sm text-destructive font-medium">
                        <AlertCircle className="w-4 h-4" /> {doc.errors}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={cn(
                        "text-xs font-medium px-2 py-1 rounded-full",
                        doc.priority === "High" ? "bg-destructive/10 text-destructive" :
                        doc.priority === "Medium" ? "bg-amber-500/10 text-amber-500" :
                        "bg-muted text-muted-foreground"
                      )}>
                        {doc.priority}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Clock className="w-3.5 h-3.5" /> {doc.waitTime}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity" asChild>
                        <Link href={`/documents/${doc.id}`}>
                          Review <ArrowRight className="w-4 h-4 ml-1" />
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {filteredQueue.length === 0 && (
                  <TableRow className="hover:bg-transparent">
                    <TableCell colSpan={6}>
                      <EmptyState
                        icon={CheckCircle2}
                        title="Queue is clear"
                        description="No documents currently require human review. Great work!"
                      />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
