"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  ArrowLeft, CheckCircle2, XCircle, AlertCircle, Save,
  Search, ZoomIn, ZoomOut, Maximize, RotateCw, History,
  FileText, Check, ChevronDown, ListChecks, Fingerprint, Network
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

// Mock extracted data
const extractedData = {
  invoice_number: { value: "INV-2024-0042", confidence: 98, status: "valid" },
  date: { value: "2024-10-24", confidence: 95, status: "valid" },
  vendor_name: { value: "TechCorp Solutions LLC", confidence: 82, status: "valid" },
  total_amount: { value: "$14,500.00", confidence: 45, status: "review" },
  tax_amount: { value: "$1,160.00", confidence: 68, status: "review" },
  currency: { value: "USD", confidence: 99, status: "valid" }
};

const metadata = {
  model: "Invoice Pro v2.1",
  processingTime: "1.2s",
  pages: 1,
  language: "en-US",
  fileSize: "1.4 MB"
};

const timeline = [
  { time: "10:42:01", event: "Document uploaded via API" },
  { time: "10:42:05", event: "OCR preprocessing started" },
  { time: "10:42:12", event: "Text extraction completed" },
  { time: "10:42:15", event: "Entity linking applied (Invoice Pro)" },
  { time: "10:42:16", event: "Validation rules triggered" },
  { time: "10:42:17", event: "Flagged for human review (confidence < 80%)", alert: true }
];

export default function DocumentWorkspacePage() {
  const [activeTab, setActiveTab] = useState("extracted");
  const [zoom, setZoom] = useState(100);

  return (
    <div className="flex flex-col h-full overflow-hidden bg-background">
      {/* Workspace Header */}
      <header className="h-14 shrink-0 border-b flex items-center justify-between px-4 bg-card/50 backdrop-blur-sm z-10">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" asChild>
            <Link href="/review"><ArrowLeft className="w-4 h-4" /></Link>
          </Button>
          <div className="flex items-center gap-3 border-l pl-4">
            <Badge variant="warning" className="uppercase text-[10px]">Review Mode</Badge>
            <div>
              <h1 className="text-sm font-semibold leading-none">Invoice_XCorp_Q3.pdf</h1>
              <p className="text-xs text-muted-foreground mt-0.5 font-mono">DOC-8922</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2 h-8">
            <XCircle className="w-4 h-4 text-destructive" /> Reject
          </Button>
          <Button variant="outline" size="sm" className="gap-2 h-8 border-amber-500/30 text-amber-500 hover:bg-amber-500/10">
            <AlertCircle className="w-4 h-4" /> Request Changes
          </Button>
          <Button size="sm" className="gap-2 h-8 bg-green-600 hover:bg-green-700 text-white">
            <CheckCircle2 className="w-4 h-4" /> Approve & Finalize
          </Button>
        </div>
      </header>

      {/* Main Workspace Area */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          
          {/* Left Panel: Document Viewer */}
          <ResizablePanel defaultSize={55} minSize={30}>
            <div className="h-full flex flex-col bg-muted/30">
              {/* Viewer Toolbar */}
              <div className="h-10 shrink-0 border-b flex items-center justify-between px-2 bg-card/50">
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground"><ListChecks className="w-4 h-4" /></Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-primary bg-primary/10"><Fingerprint className="w-4 h-4" /></Button>
                </div>
                <div className="flex items-center gap-1 bg-background rounded-md border p-0.5">
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setZoom(z => Math.max(50, z - 10))}><ZoomOut className="w-3.5 h-3.5" /></Button>
                  <span className="text-xs font-medium w-12 text-center">{zoom}%</span>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setZoom(z => Math.min(200, z + 10))}><ZoomIn className="w-3.5 h-3.5" /></Button>
                  <div className="w-px h-4 bg-border mx-1" />
                  <Button variant="ghost" size="icon" className="h-6 w-6"><Maximize className="w-3.5 h-3.5" /></Button>
                  <Button variant="ghost" size="icon" className="h-6 w-6"><RotateCw className="w-3.5 h-3.5" /></Button>
                </div>
              </div>

              {/* PDF Viewer Mock */}
              <ScrollArea className="flex-1 bg-neutral-900/5 dark:bg-black/40 relative">
                <div className="absolute inset-0 flex items-center justify-center p-8">
                  <motion.div 
                    className="bg-white shadow-2xl relative transition-transform duration-200"
                    style={{ 
                      width: "600px", 
                      height: "800px", 
                      transform: `scale(${zoom / 100})`,
                      transformOrigin: "center center"
                    }}
                  >
                    {/* Simulated Document Content */}
                    <div className="absolute top-12 left-12 right-12 bottom-12 border-2 border-neutral-100 p-8 space-y-6">
                      <div className="flex justify-between items-start border-b-2 border-neutral-200 pb-6">
                        <div className="space-y-2">
                          <h2 className="text-3xl font-bold text-neutral-800">INVOICE</h2>
                          <div className="w-32 h-4 bg-neutral-200 rounded" />
                          <div className="w-24 h-3 bg-neutral-200 rounded" />
                        </div>
                        <div className="text-right space-y-2">
                          <div className="w-40 h-8 bg-neutral-200 rounded ml-auto" />
                          <div className="w-24 h-4 bg-neutral-200 rounded ml-auto" />
                        </div>
                      </div>

                      {/* Mock OCR Bounding Boxes */}
                      <div className="absolute top-[80px] left-[400px] border-2 border-green-500 bg-green-500/20 px-1 py-0.5 text-[10px] text-green-700 font-bold">
                        INV-2024-0042
                      </div>
                      
                      <div className="absolute top-[130px] left-[50px] border-2 border-green-500 bg-green-500/20 px-1 py-0.5 text-[10px] text-green-700 font-bold">
                        TechCorp Solutions LLC
                      </div>

                      <div className="absolute bottom-[200px] right-[50px] border-2 border-red-500 bg-red-500/20 px-1 py-0.5 text-[10px] text-red-700 font-bold animate-pulse">
                        $14,500.00
                      </div>

                      <div className="absolute bottom-[240px] right-[50px] border-2 border-amber-500 bg-amber-500/20 px-1 py-0.5 text-[10px] text-amber-700 font-bold">
                        $1,160.00
                      </div>

                      {/* Line Items Mock */}
                      <div className="mt-12 space-y-4">
                        <div className="flex justify-between border-b border-neutral-200 pb-2">
                          <div className="w-1/2 h-4 bg-neutral-200 rounded" />
                          <div className="w-1/4 h-4 bg-neutral-200 rounded" />
                        </div>
                        <div className="flex justify-between">
                          <div className="w-1/2 h-3 bg-neutral-100 rounded" />
                          <div className="w-1/4 h-3 bg-neutral-100 rounded" />
                        </div>
                        <div className="flex justify-between">
                          <div className="w-1/3 h-3 bg-neutral-100 rounded" />
                          <div className="w-1/5 h-3 bg-neutral-100 rounded" />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </ScrollArea>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle />

          {/* Right Panel: Data & Review */}
          <ResizablePanel defaultSize={45} minSize={30}>
            <div className="h-full flex flex-col bg-card">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col h-full">
                <div className="h-10 shrink-0 border-b px-2 flex items-center justify-between">
                  <TabsList className="h-8 bg-transparent p-0">
                    <TabsTrigger value="extracted" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none text-xs rounded-sm px-3">
                      Extracted Data
                    </TabsTrigger>
                    <TabsTrigger value="metadata" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none text-xs rounded-sm px-3">
                      Metadata
                    </TabsTrigger>
                    <TabsTrigger value="timeline" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none text-xs rounded-sm px-3">
                      Timeline
                    </TabsTrigger>
                  </TabsList>
                  <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
                    <History className="w-3.5 h-3.5" /> Version History
                  </Button>
                </div>

                <div className="flex-1 overflow-hidden">
                  {/* Extracted Data Tab */}
                  <TabsContent value="extracted" className="h-full m-0 data-[state=inactive]:hidden">
                    <ScrollArea className="h-full">
                      <div className="p-4 space-y-6">
                        
                        {/* Validation Alert */}
                        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 flex items-start gap-3">
                          <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                          <div>
                            <h4 className="text-sm font-medium text-amber-500">Validation Warnings (2)</h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              Low confidence detected on financial totals. Please verify against document.
                            </p>
                          </div>
                        </div>

                        <div className="space-y-4">
                          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                            <FileText className="w-4 h-4" /> Header Information
                          </h3>
                          
                          <div className="space-y-3">
                            {Object.entries(extractedData).map(([key, data]) => (
                              <div key={key} className="space-y-1.5 group">
                                <div className="flex justify-between items-center">
                                  <Label className="text-xs text-muted-foreground capitalize flex items-center gap-2">
                                    {key.replace("_", " ")}
                                    {data.status === "review" && <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />}
                                  </Label>
                                  <span className={cn(
                                    "text-[10px] font-mono",
                                    data.confidence > 90 ? "text-green-500" :
                                    data.confidence > 70 ? "text-amber-500" : "text-red-500"
                                  )}>
                                    {data.confidence}% conf
                                  </span>
                                </div>
                                <div className="relative">
                                  <Input 
                                    defaultValue={data.value}
                                    className={cn(
                                      "bg-background/50 h-9 text-sm focus-visible:ring-primary/50",
                                      data.status === "review" && "border-red-500/50 bg-red-500/5"
                                    )}
                                  />
                                  {data.status === "valid" && (
                                    <Check className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500 opacity-50" />
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </ScrollArea>
                  </TabsContent>

                  {/* Metadata Tab */}
                  <TabsContent value="metadata" className="h-full m-0 p-4 data-[state=inactive]:hidden">
                    <Card className="shadow-none border-dashed bg-transparent">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Network className="w-4 h-4" /> Document Context
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Accordion type="single" collapsible defaultValue="system" className="w-full">
                          <AccordionItem value="system">
                            <AccordionTrigger className="text-sm py-2">System Metadata</AccordionTrigger>
                            <AccordionContent>
                              <div className="space-y-2 pt-2">
                                {Object.entries(metadata).map(([key, value]) => (
                                  <div key={key} className="flex justify-between text-xs">
                                    <span className="text-muted-foreground capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                                    <span className="font-mono text-foreground">{value}</span>
                                  </div>
                                ))}
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                          <AccordionItem value="custom">
                            <AccordionTrigger className="text-sm py-2">Custom Variables</AccordionTrigger>
                            <AccordionContent>
                              <div className="text-xs text-muted-foreground pt-2 italic">
                                No custom tags appended.
                              </div>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  {/* Timeline Tab */}
                  <TabsContent value="timeline" className="h-full m-0 data-[state=inactive]:hidden">
                    <ScrollArea className="h-full">
                      <div className="p-6 space-y-6">
                        <div className="relative border-l border-muted ml-3 space-y-6">
                          {timeline.map((item, i) => (
                            <div key={i} className="relative pl-6">
                              <div className={cn(
                                "absolute -left-1.5 top-1.5 w-3 h-3 rounded-full border-2 border-background",
                                item.alert ? "bg-amber-500" : "bg-primary"
                              )} />
                              <div className="flex flex-col">
                                <span className="text-[10px] font-mono text-muted-foreground">{item.time}</span>
                                <span className={cn(
                                  "text-sm font-medium mt-0.5",
                                  item.alert && "text-amber-500"
                                )}>
                                  {item.event}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </ScrollArea>
                  </TabsContent>
                </div>

              </Tabs>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  );
}
